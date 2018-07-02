import fire
import requests
import sys
from tqdm import tqdm
from contextlib import closing


class ODE(object):
    """ class to hold ode downloading commands """

    def __init__(self, https=True, debug=False):
        self.https   = https
        if https:
            self.ode_url = "https://oderest.rsl.wustl.edu/live2"
        else:
            self.ode_url = "http://oderest.rsl.wustl.edu/live2"

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

        pid: product ID of the CTX EDR, partial IDs ok
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
            for product in products:
                download_edr_img_files(product, self.https, chunk_size)

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


def query_params(self, params, key, def_value, short_hand=None):
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


def download_edr_img_files(product, https, chunk_size):
    edr_products = product['Product_files']['Product_file']
    edr_files = [x for x in edr_products if x['URL'].endswith(".IMG")]
    for edr in edr_files:
        url   = edr['URL']
        if https:
            url = url_https(url)
        filename = edr['FileName']
        # make download request
        download_file(url, filename, chunk_size)


def download_file(url, filename, chunk_size):
    with closing(requests.get(url, stream=True)) as r:
        with open(filename, "wb") as output:
            for chunk in tqdm(r.iter_content(chunk_size), desc=f'Downloading {filename}'):
                if chunk:
                    output.write(chunk)


def main():
    fire.Fire(ODE)


if __name__ == '__main__':
    main()
