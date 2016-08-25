#!/bin/env python3
# -*- coding: utf-8 -*-

import http.client
import html.parser
import copy
import json


class IndeedParser(html.parser.HTMLParser):
    def __init__(self, *kwargs):
        self.offer_entries = []
        self.offer_entry = None
        self.data_handler = None
        self.starttag_handlers = {"div": self.handle_startdiv,
                                  "a": self.handle_starta,
                                  "span": self.handle_startspan}
        self.next_starthandler = None
        self.next_pages = []
        self.is_handling_data = False
        super().__init__()

    def handle_endtag(self, tag):
        if tag == "span" and self.is_handling_data is True:
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
            classes = attrs["class"].split()
            if len(classes) > 0 and classes[0] == "row" and \
                            classes[1] == "result":
                self.offer_entry = {}
                self.offer_entries.append(self.offer_entry)

    def handle_starta(self, attrs):
        if "itemprop" in attrs and attrs["itemprop"] == "title" and \
                        "data-tn-element" in attrs and \
                        attrs["data-tn-element"] == "jobTitle" and \
                        "href" in attrs and "title" in attrs:
            self.offer_entry["link"] = "http://www.indeed.fr" + attrs["href"]
            self.offer_entry["title"] = attrs["title"]
        elif "href" in attrs and \
                attrs["href"].startswith("/emplois?q=informatique&l=Rennes+%2835%29&radius=5&jt=internship&sort=date&start=") and not \
                attrs["href"].endswith("&pp="):
            self.next_pages.append(attrs["href"])

    def handle_startspan(self, attrs):
        if "itemprop" in attrs:
            if attrs["itemprop"] == "name":
                self.data_handler = self.handle_organisation
            elif attrs["itemprop"] == "description":
                self.data_handler = self.handle_summary
                self.is_handling_data = True

    def handle_data(self, data):
        if self.data_handler is not None:
            self.data_handler(data)
            if self.is_handling_data is False:
                self.data_handler = None

    def handle_organisation(self, data):
        self.offer_entry["organisation"] = data.replace("\n", "").strip()

    def handle_summary(self, data):
        if "summary" not in self.offer_entry:
            self.offer_entry["summary"] = data
        else:
            self.offer_entry["summary"] = self.offer_entry["summary"] + data


def parse_indeed_offers():
    offer_entries = []
    parser = IndeedParser()
    url = "/emplois?q=informatique&l=Rennes+(35)&radius=5&jt=internship&sort=date"
    indeed_connection = http.client.HTTPConnection("www.indeed.fr")
    indeed_connection.connect()
    indeed_connection.request("GET", url)
    indeed_response = indeed_connection.getresponse()
    parser.feed(indeed_response.read().decode("utf-8"))
    indeed_connection.close()
    next_urls = copy.deepcopy(parser.next_pages)
    offer_entries = offer_entries + parser.offer_entries
    for next_url in next_urls:
        parser = IndeedParser()
        indeed_connection = http.client.HTTPConnection("www.indeed.fr")
        indeed_connection.connect()
        indeed_connection.request("GET", next_url)
        indeed_response = indeed_connection.getresponse()
        if indeed_response.getcode() == 301:
            actual_url = indeed_response.getheader("Location")
            indeed_connection.close()
            if actual_url is None:
                continue
            indeed_connection = http.client.HTTPConnection("www.indeed.fr")
            indeed_connection.connect()
            indeed_connection.request("GET", actual_url)
            indeed_response = indeed_connection.getresponse()
        page = indeed_response.read().decode("utf-8")
        parser.feed(page)
        indeed_connection.close()
        offer_entries = offer_entries + parser.offer_entries
    return offer_entries


def indeed_offers_to_json():
    return json.dumps(parse_indeed_offers())

if __name__ == "__main__":
    print(indeed_offers_to_json().encode("utf-8"))
