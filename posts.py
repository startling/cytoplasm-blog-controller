# -*- Coding: utf-8 -*-

import yaml
import urllib
import re
import datetime
import os
from StringIO import StringIO
from collections import defaultdict
from cytoplasm.interpreters import interpret, interpret_filelike

class Post(object):
    def __init__(self, controller, path):
        "Initalize a post object given the source file."
        self.path = path
        # a defaultdict of metadata; values default to None
        self.metadata = defaultdict(lambda: None)
        # initialize the list of tags, so it defaults to [].
        self.metadata["tags"] = []
        # read the metadata and update the `metadata` attribute with it.
        meta, contents = self._parse_metadata()
        self.metadata.update(meta)
        # get a datetime object from the "date" metadata
        self.date = datetime.datetime.strptime(self.metadata["date"],
                "%Y/%m/%d")
        # get these to be nice...
        self.year = self.date.year
        self.month = self.date.month
        self.monthname = self.date.strftime("%B")
        self.day = self.date.day
        # This is a whitespace-free version of the name, to be used in things
        # like filenames.
        if self.metadata["slug"] == None:
            # if the slug != None, then the user has defined it in the metadata
            # and we should not override it.
            self.metadata["slug"] = urllib.quote(self.title.replace(" ", "-"))
        # this is the relative url for the post, relative from the destination
        # directory:
        self.url = os.path.join(str(self.year), str(self.month), self.slug + 
                ".html")
        # Interpret the file.
        suffix = self.path.split(".")[-1]
        # this is given a StringIO object because interpreters expect
        # file-like objects. The StringIO object is based on the contents
        # we read from the file earlier -- i.e., the file without the metadata
        interpret_filelike(StringIO(contents), self, controller.site, suffix)

    def __getattr__(self, name):
        "If there's no such instance attribute, look in the post metadata."
        return self.metadata[name]

    def close(self):
        # This is just here so that python doesn't throw up an error when
        # something else thinks this is a file.
        pass

    def write(self, s):
        # instead of writing to disk when this is written to , simply change
        # the contents attribute.
        self.contents = s.decode("utf8")

    def _parse_metadata(self):
        "Read the metadata for file `self.path` from it's yaml header."
        with open(self.path, "r") as f:
            contents = f.read()
        # get everything that looks like:
        # some_stuff: thing
        #
        # contents
        separated = re.match(r'(.+?\:.+?)\n\n(.*)', contents, flags=re.DOTALL)
        # if there's no match, raise an error.
        if separated == None:
            raise ControllerError("Post '%s' has no commented metadata."
                    % (self.path))
        # otherwise, get yaml data from the first matching group (there should
        # be only one anyway).
        meta = yaml.load(separated.group(1))
        # raise an error if there's no title in the metadata
        if "title" not in meta.keys():
            raise ControllerError(
                    "Post '%s' doesn't have a title in its metadata."
                    % (self.path))
        # raise an error if there's no date in the metadata:
        if "date" not in meta.keys():
            raise ControllerError(
                    "Post '%s' doesn't have a date in its metadata."
                    % (self.path))
        return meta, separated.group(2)
