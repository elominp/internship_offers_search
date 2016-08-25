#!/bin/env python3
# -*- coding: utf-8 -*-

import http.client
import html.parser
import copy
import json


class JobIsJobParser(html.parser.HTMLParser):
    def __init__(self, *kwargs):
        self.offer_entries = []
        self.offer_entry = None
        self.data_handler = None
        self.starttag_handlers = {"div": self.handle_startdiv,
                                  "a": self.handle_starta,
                                  "strong": self.handle_startstrong,
                                  "p": self.handle_startp,
                                  "span": self.handle_startspan}
        self.next_starthandler = None
        self.next_pages = []
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag in self.starttag_handlers:
            self.starttag_handlers[tag](dict(attrs))
        elif self.next_starthandler is not None:
            self.next_starthandler(tag, dict(attrs))
            self.next_starthandler = None

    def handle_startdiv(self, attrs):
        if "class" in attrs:
            classes = attrs["class"].split()
            if len(classes) > 0 and classes[0] == "offer_list":
                self.offer_entry = {}
                self.offer_entries.append(self.offer_entry)

    def handle_starta(self, attrs):
        if "itemprop" in attrs and attrs["itemprop"] == "title":
            self.data_handler = self.handle_title
            if "href" in attrs:
                self.offer_entry["link"] = attrs["href"]
        elif "class" in attrs and attrs["class"] == "company-page":
            self.data_handler = self.handle_organisation
        elif "href" in attrs and attrs["href"].startswith(
                "http://www.jobisjob.fr/search?what=stage&where=rennes&category=IT&jobType=Stage&order=date&page="):
            url = attrs["href"]
            if url not in self.next_pages:
                self.next_pages.append(url)

    def handle_startstrong(self, attrs):
        if "itemprop" in attrs and attrs["itemprop"] == "name" and \
                    "organisation" not in self.offer_entry:
            self.data_handler = self.handle_organisation

    def handle_startp(self, attrs):
        if "class" in attrs and attrs["class"] == "description":
            self.data_handler = self.handle_summary

    def handle_startspan(self, attrs):
        if "class" in attrs and attrs["class"] == "date" and \
                    "itemprop" in attrs and attrs["itemprop"] == "datePosted":
            self.data_handler = self.handle_date

    def handle_data(self, data):
        if self.data_handler is not None:
            self.data_handler(data)
            self.data_handler = None

    def handle_date(self, data):
        self.offer_entry["date"] = data

    def handle_summary(self, data):
        self.offer_entry["summary"] = data

    def handle_title(self, data):
        self.offer_entry["title"] = data

    def handle_organisation(self, data):
        self.offer_entry["organisation"] = data


def parse_jobisjob_offers():
    offer_entries = []
    parser = JobIsJobParser()
    url = "/search?what=stage&where=rennes&category=IT&jobType=Stage"
    jobisjob_connection = http.client.HTTPConnection(
            "www.jobisjob.fr")
    jobisjob_connection.connect()
    jobisjob_connection.request("GET", url)
    jobisjob_response = jobisjob_connection.getresponse()
    page = jobisjob_response.read().decode("utf-8")
    parser.feed(page)
    jobisjob_connection.close()
    next_urls = copy.deepcopy(parser.next_pages)
    offer_entries = offer_entries + parser.offer_entries
    for next_url in next_urls:
        parser = JobIsJobParser()
        jobisjob_connection = http.client.HTTPConnection(
                "www.jobisjob.fr")
        jobisjob_connection.connect()
        jobisjob_connection.request("GET", next_url)
        jobisjob_response = jobisjob_connection.getresponse()
        if jobisjob_response.getcode() == 301:
            actual_url = jobisjob_response.getheader("Location")
            jobisjob_connection.close()
            if actual_url is None:
                continue
            jobisjob_connection = http.client.HTTPConnection(
                    "www.jobisjob.fr")
            jobisjob_connection.connect()
            jobisjob_connection.request("GET", actual_url)
            jobisjob_response = jobisjob_connection.getresponse()
        page = jobisjob_response.read().decode("utf-8")
        parser.feed(page)
        jobisjob_connection.close()
        offer_entries = offer_entries + parser.offer_entries
    return offer_entries


def jobisjob_offers_to_json():
    return json.dumps(parse_jobisjob_offers())

if __name__ == "__main__":
    print(jobisjob_offers_to_json().encode("utf-8"))
