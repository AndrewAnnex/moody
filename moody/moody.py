"""
The MIT License (MIT)

Copyright (c) [2017-2021] [Andrew Annex]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import fire
import requests
import sys
from tqdm import tqdm
from contextlib import closing
from typing import Optional
import shutil
import os
from multiprocessing import Pool, cpu_count
from functools import partial
from itertools import chain


class ODE(object):
    """ class to hold ode downloading commands """

    def __init__(self, https=True, debug=False):
        self.https   = https
        if https:
            self.ode_url = "https://oderest.rsl.wustl.edu/live2"
            self.gds_url = "https://oderest.rsl.wustl.edu/livegds"
        else:
            self.ode_url = "http://oderest.rsl.wustl.edu/live2"
            self.gds_url = "http://oderest.rsl.wustl.edu/livegds"

    def ctx_edr(self, pid, chunk_size=1024*1024):
        """
        Download a CTX EDR .IMG file to the CWD.

        pid: product ID of the CTX EDR, partial IDs ok
        chunk_size: Chunk size in bytes to use in download
        """
        productid = "{}*".format(pid)

        query = {"target"    : "mars",
                 "query"     : "product",
                 "results"   : "f",
                 "output"    : "j",
                 "pt"        : "EDR",
                 "iid"       : "CTX",
                 "ihid"      : "MRO",
                 "productid" : productid}

        # Query the ODE
        product = query_ode(self.ode_url, query)
        # Validate query results with conditions for this particular query
        if isinstance(product, list):
            print("Error: Too many products selected for in query, Make PID more specific")
            sys.exit(1)
        else:
            download_edr_img_files(product, self.https, chunk_size)

    def hirise_edr(self, pid, chunk_size=1024*1024):
        """
        Download a HiRISE EDR set of .IMG files to the CWD

        You must know the full id to specifiy the filter to use, ie:
        PSP_XXXXXX_YYYY         will download every EDR IMG file available
        PSP_XXXXXX_YYYY_R       will download every EDR RED filter IMG file
        PSP_XXXXXX_YYYY_BG12_0  will download only the BG12_0

        As a wild card is auto applied to the end of the provided pid

        pid: product ID of the HiRISE EDR, partial IDs ok
        chunk_size: Chunk size in bytes to use in download
        """
        productid = "{}*".format(pid)

        query = {"target"    : "mars",
                 "query"     : "product",
                 "results"   : "f",
                 "output"    : "j",
                 "pt"        : "EDR",
                 "iid"       : "HiRISE",
                 "ihid"      : "MRO",
                 "productid" : productid}

        # Query the ODE
        products = query_ode(self.ode_url, query)
        # Validate query results with conditions for this particular query
        if len(products) > 30:
            print("Error: Too many products selected for in query, Make PID more specific")
            sys.exit(1)
        if not isinstance(products, list):
            print("Error: Too few responses from server to be a full HiRISE EDR, ")
        else:
            # proceed to download
            download_edr_img_files_par(products, self.https, chunk_size)
                
    def lrocnac_edr(self, pid, chunk_size=1024*1024):
        """
        Download a LROC NAC EDR set of .IMG files to the CWD

        As a wild card is auto applied to the end of the provided pid

        pid: product ID of the LROC EDR, partial IDs ok
        chunk_size: Chunk size in bytes to use in download
        """
        productid = "{}*".format(pid)

        query = {"target"    : "moon",
                 "query"     : "product",
                 "results"   : "f",
                 "output"    : "j",
                 "pt"        : "EDRNAC",
                 "iid"       : "LROC",
                 "ihid"      : "LRO",
                 "productid" : productid}

        # Query the ODE
        products = query_ode(self.ode_url, query)
        # Validate query results with conditions for this particular query
        if len(products) > 30:
            print("Error: Too many products selected for in query, Make PID more specific")
            sys.exit(1)
        if not isinstance(products, list):
            print("Error: Too few responses from server to be a full HiRISE EDR, ")
        else:
            # proceed to download
            download_edr_img_files_par(products, self.https, chunk_size)

    def pedr(self, minlon: float, minlat: float, maxlon: float, maxlat: float, wkt_footprint: Optional[str] = None, ext: str = 'csv', **kwargs):
        """
        Get the mola pedr csv/shp file for the query bounds
        :param ext:
        :param minlon: minimum longitude (western most longitude)
        :param minlat: minimum latitude  (southern most latitude)
        :param maxlon: maximum longitude (eastern most longitude)
        :param maxlat: maximum latitude  (northern most latitude)
        :param wkt_footprint: Optional WKT footprint to further filter out points
        :return:
        """
        if minlon < 0 or maxlon < 0:
            # convert -180 to 180 to 0 to 360
            minlon += 180.0
            maxlon += 180.0
        assert 0 <= minlon <= 360
        assert 0 <= maxlon <= 360
        assert minlon < maxlon and minlat < maxlat
        # default is csv
        rt = 's' if ext == 'shp' else 'v'
        query = {
            "query": "molapedr",
            "results": rt,
            "output": "J",
            "minlat": str(minlat),
            "maxlat": str(maxlat),
            "westernlon": str(minlon),
            "easternlon": str(maxlon),
            "zipclean": 't',
            **kwargs
        }
        if wkt_footprint:
            query['footprint'] = f'{wkt_footprint}'
        # Query the ODEq
        response = query_gds(self.gds_url, query)
        # get the ResultFile, it seems ResultFile has the same number of contents as Number Files
        resultfile = response['ResultFiles']['ResultFile']
        if isinstance(resultfile, dict):
            resultfile = [resultfile]
        for f in resultfile:
            fname = str(f['URL'].split('/')[-1])
            fname = fname.replace('-', '__neg__')
            download_file(f['URL'], fname, 1024)

    def get_meta(self, **kwargs):
        """
        Perform a mostly arbitrary meta_data query and dump to std out
        :param kwargs:
        :return:
        """
        query = kwargs
        # filters
        query = query_params(query, 'productid', None, short_hand='pid')
        query = query_params(query, 'query', 'product')
        query = query_params(query, 'results', 'm')
        query = query_params(query, 'output', 'j')
        return query_ode(self.ode_url, query=query)

    def get_meta_by_key(self, key, **kwargs):
        res = self.get_meta(**kwargs)
        return res[key]

    def get_ctx_meta(self, pid):
        productid = "{}*".format(pid)

        query = {"target"   : "mars",
                 "query"    : "product",
                 "results"  : "m",
                 "output"   : "j",
                 "pt"       : "EDR",
                 "iid"      : "CTX",
                 "ihid"     : "MRO",
                 "productid": productid}

        return query_ode(self.ode_url, query=query)

    def get_ctx_meta_by_key(self, pid, key):
        res = self.get_ctx_meta(pid)
        return res[key]

    def get_hirise_meta(self, pid):
        productid = "{}*".format(pid)

        query = {"target"   : "mars",
                 "query"    : "product",
                 "results"  : "m",
                 "output"   : "j",
                 "pt"       : "RDRV11",
                 "iid"      : "HiRISE",
                 "ihid"     : "MRO",
                 "productid": productid}

        return query_ode(self.ode_url, query=query)

    def get_hirise_meta_by_key(self, pid, key):
        res = self.get_hirise_meta(pid)
        return res[key]


def url_https(url):
    return url.replace("http://", "https://")


def query_params(params, key, def_value, short_hand=None):
    """
    updates params dict to use
    :param params:
    :param key:
    :param def_value:
    :param short_hand:
    :return:
    """
    if key not in params and short_hand:
        # value is associated with shorthand, move to key
        params[key] = params.get(short_hand, def_value)
        del params[short_hand]
    elif key not in params and not short_hand:
        params[key] = def_value
    elif key in params:
        # key is there, also possibly shorthand
        # assume def value at this point is not needed
        if short_hand in params:
            del params[short_hand]
    return params


def query_gds(gds_url, query):
    with closing(requests.get(gds_url, params=query)) as r:
        if r.ok:
            response = r.json()
            products_check = response['GDSResults']
            if products_check['Status'] != 'Success':
                raise RuntimeError(f"Error, some issue with the query: {r.url}", products_check)
            else:
                return products_check
        else:
            raise RuntimeError("Error with query at url: {} with code: {}".format(gds_url, r.status_code))


def query_ode(ode_url, query):
    with closing(requests.get(ode_url, params=query)) as r:
        if r.ok:
            response = r.json()
            products_check = response['ODEResults']['Products']
            if products_check == "No Products Found":
                print("Error, PID not found by ODE")
                sys.exit(1)
            else:
                return products_check['Product']
        else:
            print("Error with query at url: {} with code: {}".format(ode_url, r.status_code))
            sys.exit(1)


def download_edr_img_files_par(products, https: bool = True, chunk_size: int = 1024*1024):
    edr_products = list(chain.from_iterable([_['Product_files']['Product_file'] for _ in products]))
    edr_files = [x for x in edr_products if x['URL'].endswith(".IMG")]
    # fix lroc urls
    for x in edr_files:
        if 'www.lroc.asu.edu' in x['URL']:
            x['URL'] = x['URL'].replace('www.lroc.asu.edu', 'pds.lroc.asu.edu')
    urls = [_['URL'] for _ in edr_files]
    filenames = [_['FileName'] for _ in edr_files]
    with Pool(cpu_count()) as pool:
        get = partial(download_file, chunk_size=chunk_size)
        pool.starmap(get, list(zip(urls, filenames)))


def download_edr_img_files(product, https, chunk_size):
    edr_products = product['Product_files']['Product_file']
    edr_files = [x for x in edr_products if x['URL'].endswith(".IMG")]
    # fix lroc urls
    for x in edr_files:
        if 'www.lroc.asu.edu' in x['URL']:
            x['URL'] = x['URL'].replace('www.lroc.asu.edu', 'pds.lroc.asu.edu')
    for edr in edr_files:
        url   = edr['URL']
        if https:
            url = url_https(url)
        filename = edr['FileName']
        # make download request
        download_file(url, filename, chunk_size)


def download_file(url, filename, chunk_size):
    with open(filename, "wb", chunk_size) as output:
        with closing(requests.get(url, stream=True)) as r:
            for chunk in tqdm(r.iter_content(chunk_size), desc=f'Downloading {filename}'):
                if chunk:
                    output.write(chunk)
                    output.flush()
            r.close()
        output.flush()
    if str(filename).endswith('.zip'):
        shutil.unpack_archive(filename)
        if os.path.exists(filename):
            os.remove(filename)


def main():
    fire.Fire(ODE)


if __name__ == '__main__':
    main()
