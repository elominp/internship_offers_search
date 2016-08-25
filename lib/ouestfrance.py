#!/bin/env python3
# -*- coding: utf-8 -*-

import http.client
import html.parser
import copy
import json


class OuestFranceParser(html.parser.HTMLParser):
    def __init__(self, *kwargs):
        self.offer_entries = []
        self.offer_entry = None
        self.data_handler = None
        self.starttag_handlers = {"div": self.handle_startdiv,
                                  "li": self.handle_startli,
                                  "meta": self.handle_startmeta}
        self.next_starthandler = None
        self.next_pages = []
        self.is_handling_data = False
        super().__init__()

    def handle_endtag(self, tag):
        if tag == "div" and self.is_handling_data is True:
            self.is_handling_data = False
            self.data_handler = None

    def handle_starttag(self, tag, attrs):
        if tag in self.starttag_handlers:
            self.starttag_handlers[tag](dict(attrs))
        elif self.next_starthandler is not None:
            self.next_starthandler(tag, dict(attrs))
            self.next_starthandler = None

    def handle_startdiv(self, attrs):
        if "class" in attrs:
            if attrs["class"] == "date":
                self.data_handler = self.handle_date
            elif attrs["class"] == "teaser" and "itemprop" in attrs and \
                        attrs["itemprop"] == "description":
                self.data_handler = self.handle_summary

    def handle_startli(self, attrs):
        if "class" in attrs and attrs["class"] == "uneAnn cf":
            self.offer_entry = {}
            self.offer_entries.append(self.offer_entry)
            if "onclick" in attrs:
                url = attrs["onclick"].replace("document.location=('", "")
                url = url.replace("');", "")
                url = "https://www.ouestfrance-emploi.com" + url
                self.offer_entry["link"] = url

    def handle_startmeta(self, attrs):
        if "itemprop" in attrs:
            if attrs["itemprop"] == "name" and \
                    "content" in attrs:
                self.offer_entry["organisation"] = attrs["content"]
            elif attrs["itemprop"] == "title" and "content" in attrs:
                self.offer_entry["title"] = attrs["content"]

    def handle_data(self, data):
        if self.data_handler is not None:
            self.data_handler(data)
            if self.is_handling_data is False:
                self.data_handler = None

    def handle_date(self, data):
        self.offer_entry["date"] = data

    def handle_summary(self, data):
        if "summary" not in self.offer_entry:
            self.offer_entry["summary"] = data
        else:
            self.offer_entry["summary"] = self.offer_entry["summary"] + data


def parse_ouest_france_offers():
    offer_entries = []
    parser = OuestFranceParser()
    url = "/recherche-emploi/rennes-?f[contrat]=Stage&f[ville]=Rennes"
    ouest_france_connection = http.client.HTTPSConnection(
            "www.ouestfrance-emploi.com")
    ouest_france_connection.connect()
    ouest_france_connection.request("GET", url)
    ouest_france_response = ouest_france_connection.getresponse()
    page = ouest_france_response.read().decode("utf-8")
    parser.feed(page)
    ouest_france_connection.close()
    next_urls = copy.deepcopy(parser.next_pages)
    offer_entries = offer_entries + parser.offer_entries
    for next_url in next_urls:
        parser = OuestFranceParser()
        ouest_france_connection = http.client.HTTPSConnection(
                "www.ouestfrance-emploi.com")
        ouest_france_connection.connect()
        ouest_france_connection.request("GET", next_url)
        ouest_france_response = ouest_france_connection.getresponse()
        if ouest_france_response.getcode() == 301:
            actual_url = ouest_france_response.getheader("Location")
            ouest_france_connection.close()
            if actual_url is None:
                continue
            ouest_france_connection = http.client.HTTPSConnection(
                    "www.ouestfrance-emploi.com")
            ouest_france_connection.connect()
            ouest_france_connection.request("GET", actual_url)
            ouest_france_response = ouest_france_connection.getresponse()
        page = ouest_france_response.read().decode("utf-8")
        parser.feed(page)
        ouest_france_connection.close()
        offer_entries = offer_entries + parser.offer_entries
    return offer_entries


def ouest_france_offers_to_json():
    return json.dumps(parse_ouest_france_offers())

if __name__ == "__main__":
    print(ouest_france_offers_to_json().encode("utf-8"))
