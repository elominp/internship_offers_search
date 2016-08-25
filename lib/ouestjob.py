#!/bin/env python3
# -*- coding: utf-8 -*-

import http.client
import html.parser
import copy
import json


class OuestJobParser(html.parser.HTMLParser):
    def __init__(self, *kwargs):
        self.offer_entries = []
        self.offer_entry = None
        self.data_handler = None
        self.starttag_handlers = {"section": self.handle_startsection,
                                  "a": self.handle_starta,
                                  "strong": self.handle_startstrong,
                                  "span": self.handle_startspan}
        self.next_starthandler = None
        self.handle_title_text = False
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag in self.starttag_handlers:
            self.starttag_handlers[tag](dict(attrs))
        elif self.next_starthandler is not None:
            self.next_starthandler(tag, dict(attrs))
            self.next_starthandler = None

    def handle_startsection(self, attrs):
        if "class" in attrs and \
                attrs["class"].split()[0] == "annonce":
            self.offer_entry = {"summary": ""}
            self.offer_entries.append(self.offer_entry)

    def handle_starta(self, attrs):
        if "class" in attrs:
            classes = attrs["class"].split()
            if len(classes) > 0 and classes[0] == "lien-annonce":
                if "href" in attrs:
                    self.offer_entry["link"] = "http://www.ouestjob.com" + \
                                               attrs["href"]
                    self.handle_title_text = True

    def handle_startstrong(self, attrs):
        if self.handle_title_text is True:
            self.data_handler = self.handle_title
        self.handle_title_text = False

    def handle_startspan(self, attrs):
        if "itemprop" in attrs and attrs["itemprop"] == "name":
            self.data_handler = self.handle_organisation

    def handle_data(self, data):
        if self.data_handler is not None:
            self.data_handler(data)
            self.data_handler = None

    def handle_title(self, data):
        self.offer_entry["title"] = data

    def handle_organisation(self, data):
        self.offer_entry["organisation"] = data


def parse_ouestjob_offers():
    ouestjob_connection = http.client.HTTPConnection("www.ouestjob.com")
    ouestjob_connection.connect()
    ouestjob_connection.request("GET",
                                "/emplois/recherche.html?l=Rennes+35000&f=Informatique_dev_hard&f=Informatique_dev&f=Informatique_syst_info&f=Informatique_syst_reseaux&c=Stage")
    ouestjob_response = ouestjob_connection.getresponse()
    parser = OuestJobParser()
    parser.feed(ouestjob_response.read().decode("utf-8"))
    ouestjob_connection.close()
    return copy.deepcopy(parser.offer_entries)


def ouestjob_offers_to_json():
    return json.dumps(parse_ouestjob_offers())

if __name__ == "__main__":
    print(ouestjob_offers_to_json().encode("utf-8"))
