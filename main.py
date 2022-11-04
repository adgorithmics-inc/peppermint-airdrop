import requests
import argparse
import csv
import os
import http
import logging

logging.basicConfig(level=logging.INFO)


class API:
    URL = "https://peppermint-api.com"

    def __init__(self):
        self.token = os.environ["PEPPERMINT_API_TOKEN"]

    def get(self, path):
        res = requests.get(
            url=f"{self.URL}{path}",
        )
        return res.status_code, res.json()

    def post(self, path, data=None, files=None):
        res = requests.post(
            url=f"{self.URL}{path}",
            data=data,
            files=files,
            headers={"authorization": f"Bearer {self.token}"},
        )

        return res.status_code, res.json()


def main(medias, addresses, contract):
    api = API()
    status, res = api.get(f"/api/v2/contracts/{contract}/")

    if status != http.HTTPStatus.OK:
        raise Exception(f"Contract not found. ({status})")

    with open(medias, "r") as f:
        medias = [m[0] for m in csv.reader(f)]

    with open(addresses, "r") as f:
        addresses = [a[0] for a in csv.reader(f)]

    if len(addresses) != len(medias):
        raise Exception("Addresses and medias needs to contain same number of members.")

    for index, _ in enumerate(addresses):
        logging.info("Airdropping %s to %s", medias[index], addresses[index])
        address = addresses[0]
        media_url = medias[index]
        filename = media_url.split("/")[-1]

        status, res = api.post(
            path="/api/v2/vouchers/",
            data={
                "contract": contract,
            },
            files={"media": (filename, requests.get(media_url).content)},
        )

        if status != http.HTTPStatus.OK:
            raise Exception(f"Failed to create voucher. ({status})")

        status, res = api.post(
            path="/api/v2/tokens/exchange/",
            data={
                "code": res["code"],
                "owner": address
            },
            files={"media": (filename, requests.get(media_url).content)},
        )

        if status != http.HTTPStatus.OK:
            raise Exception(f"Failed to airdrop. ({status})")

        logging.info("Airdropped %s to %s", filename, address)


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Airdrop", description="Airdrop NFTs into wallets"
    )

    parser.add_argument("-m", "--medias", required=True)  # positional argument
    parser.add_argument("-a", "--addresses", required=True)  # option that takes a value
    parser.add_argument("-c", "--contract", required=True)  # on/off flag

    args = parser.parse_args()

    if not os.environ.get("PEPPERMINT_API_TOKEN"):
        raise EnvironmentError("PEPPERMINT_API_TOKEN not set")

    main(medias=args.medias, addresses=args.addresses, contract=args.contract)
