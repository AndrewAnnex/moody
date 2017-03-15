import fire
import requests
import sys
import progressbar
from contextlib import closing


class ODE(object):
    """ class to hold ode downloading commands """

    def __init__(self, https=True):
        self.https   = https
        if https:
            self.ode_url = "https://oderest.rsl.wustl.edu/live2"
        else:
            self.ode_url = "http://oderest.rsl.wustl.edu/live2"

    def ctx_edr(self, pid, chunk_size=1024*10000):
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

    def hirise_edr(self, pid, chunk_size=1024*10000):
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


def url_https(url):
    return url.replace("http://", "https://")


def query_ode(ode_url, query):
    with closing(requests.request("GET", ode_url, params=query)) as r:
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
        bar = progressbar.ProgressBar()
        with open(filename, "wb") as output:
            print("Downloading {}".format(filename))
            for chunk in bar(r.iter_content(chunk_size=chunk_size)):
                if chunk:
                    output.write(chunk)


def main():
    fire.Fire(ODE)

if __name__ == '__main__':
    main()
