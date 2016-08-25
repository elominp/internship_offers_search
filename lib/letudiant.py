#!/bin/env python3
# -*- coding: utf-8 -*-

import http.client
import html.parser
import copy
import json


class LEtudiantParser(html.parser.HTMLParser):
    def __init__(self, *kwargs):
        self.offer_entries = []
        self.offer_entry = None
        self.data_handler = None
        self.starttag_handlers = {"div": self.handle_startdiv,
                                  "a": self.handle_starta,
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
            if len(classes) > 0 and classes[0] == "c-block" and \
                            classes[1] == "c-search-result":
                self.offer_entry = {"summary": ""}
                self.offer_entries.append(self.offer_entry)

    def handle_starta(self, attrs):
        if "class" in attrs:
            if attrs["class"] == "c-search-result__title":
                if "href" in attrs:
                    url = "http://jobs-stages.letudiant.fr" + attrs["href"]
                    self.offer_entry["link"] = url
                self.data_handler = self.handle_title
            elif attrs["class"] == "c-pager__item" and "href" in attrs:
                self.next_pages.append(attrs["href"])

    def handle_startspan(self, attrs):
        if "class" in attrs:
            if attrs["class"] == "c-search-result__title__date":
                self.data_handler = self.handle_date
            elif attrs["class"] == " ":
                self.data_handler = self.handle_organisation

    def handle_data(self, data):
        if self.data_handler is not None:
            self.data_handler(data)
            self.data_handler = None

    def handle_title(self, data):
        self.offer_entry["title"] = data

    def handle_date(self, data):
        self.offer_entry["date"] = data.split()[2]

    def handle_organisation(self, data):
        self.offer_entry["organisation"] = data.replace("\n", "").strip()


def parse_letudiant_offers():
    offer_entries = []
    parser = LEtudiantParser()
    url = "/stages-etudiants/offres/ville-6432801/date-desc/page-1.html"
    letudiant_connection = http.client.HTTPConnection(
            "jobs-stages.letudiant.fr")
    letudiant_connection.connect()
    letudiant_connection.request("GET", url)
    letudiant_response = letudiant_connection.getresponse()
    page = letudiant_response.read().decode("utf-8")
    parser.feed(page)
    letudiant_connection.close()
    next_urls = copy.deepcopy(parser.next_pages)
    offer_entries = offer_entries + parser.offer_entries
    for next_url in next_urls:
        parser = LEtudiantParser()
        letudiant_connection = http.client.HTTPConnection(
                "jobs-stages.letudiant.fr")
        letudiant_connection.connect()
        letudiant_connection.request("GET", next_url)
        letudiant_response = letudiant_connection.getresponse()
        if letudiant_response.getcode() == 301:
            actual_url = letudiant_response.getheader("Location")
            letudiant_connection.close()
            if actual_url is None:
                continue
            letudiant_connection = http.client.HTTPConnection(
                    "jobs-stages.letudiant.fr")
            letudiant_connection.connect()
            letudiant_connection.request("GET", actual_url)
            letudiant_response = letudiant_connection.getresponse()
        page = letudiant_response.read().decode("utf-8")
        parser.feed(page)
        letudiant_connection.close()
        offer_entries = offer_entries + parser.offer_entries
    return offer_entries


def letudiant_offers_to_json():
    return json.dumps(parse_letudiant_offers())

if __name__ == "__main__":
    print(letudiant_offers_to_json().encode("utf-8"))
