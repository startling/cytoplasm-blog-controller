import os
import yaml
import re
import datetime
import cytoplasm
import urllib
from StringIO import StringIO
from operator import attrgetter
from collections import defaultdict
from cytoplasm.interpreters import interpret, interpret_filelike
from cytoplasm.errors import ControllerError


def metadata(file):
    "Read the metadata for file `file` from file.yaml."
    with open(file, "r") as f:
        contents = f.read()
    # get everything that looks like:
    # some_stuff: thing
    #
    # contents
    separated = re.match(r'(.+?\:.+?)\n\n(.*)', contents, flags=re.DOTALL)
    # if there's no match, raise an error.
    if separated == None:
        raise ControllerError("Post '%s' has no commented metadata." % (file))
    # otherwise, get yaml data from the first matching group (there should be
    # only one anyway).
    meta = yaml.load(separated.group(1))
    # raise an error if there's no title in the metadata
    if "title" not in meta.keys():
        raise ControllerError("Post '%s' doesn't have a title in its metadata."
                % (file))
    # raise an error if there's no date in the metadata:
    if "date" not in meta.keys():
        raise ControllerError("Post '%s' doesn't have a date in its metadata."
                % (file))
    return meta, separated.group(2)


class Post(object):
    "A sort-of file-like object that defines a post."
    def __init__(self, path):
        # the source file of the post
        self.path = path
        # instantiate these attributes, so they default to None.
        self.contents = None
        self.author = None
        self.email = None
        self.slug = None
        # an empty list for tags; this way, if they aren't in the metadata,
        # it defaults to this.
        self.tags = []
        # Read the metadata from this file and update this objects __dict__
        # with it; this allows the user to have arbitrary, custom fields
        # further than "title" and "date".
        # `metadata` also returns `contents`, which is the file contents
        # sans the metadata
        meta, contents = metadata(self.path)
        self.__dict__.update(meta)
        # get a datetime object from the "date" metadata
        self.date = datetime.datetime.strptime(self.date, "%Y/%m/%d")
        # get these to be nice...
        self.year = self.date.year
        self.month = self.date.month
        self.monthname = self.date.strftime("%B")
        self.day = self.date.day
        # This is a whitespace-free version of the name, to be used in things
        # like filenames.
        if self.slug == None:
            # if the slug != None, then the user has defined it in the metadata
            # and we should not override it.
            self.slug = urllib.quote(self.title.replace(" ", "-"))
        # this is the relative url for the post, relative from the destination
        # directory:
        self.url = os.path.join(str(self.year), str(self.month), self.slug + 
                ".html")
        # Interpret the file.
        suffix = self.path.split(".")[-1]
        # this is given a StringIO object because interpreters expect
        # file-like objects. The StringIO object is based on the contents
        # we read from the file earlier -- i.e., the file without the metadata
        interpret_filelike(StringIO(contents), self, suffix)

    def close(self):
        # This is just here so that python doesn't throw up an error when
        # something else thinks this is a file.
        pass

    def write(self, s):
        # instead of writing to disk when this is written to , simply change
        # the contents attribute.
        self.contents = s.decode("utf8")


class BlogController(cytoplasm.controllers.Controller):
    def __init__(self, data, destination, templates="_templates",
            posts_per_page=10):
        # take the base arguments for a controller and, optinally, the number
        # of posts per page.
        self.posts_per_page = posts_per_page
    # pass the base arguments to the base controller's __init__
        cytoplasm.controllers.Controller.__init__(self, data, destination,
                                                    templates)

    def __call__(self):
        # this is a dictionary where the values are lists of Post objects and
        # the keys are the directories where those posts should go. For
        # example, divisions["2011"] will have all the things posted in 2011.
        # There will be months, too, like divisions["2011/12"].
        # Everything will be in divisions[""].
        divisions = defaultdict(list)
        # figure out the templates to use:
        post_template = self.template("post")
        chronological_template = self.template("chronological")
        for file in os.listdir(self.data_directory):
            # instantiate the Post object
            post = Post(os.path.join(self.data_directory, file))
            # append it to the grand list of posts
            divisions[""].append(post)
            # append it to the list of posts for its year and month.
            divisions[str(post.year)].append(post)
            divisions[os.path.join(str(post.year), str(post.month))].append(
                                                                        post)
            # append the post to a division for each of its tags
            for tag in post.tags:
                divisions[tag].append(post)
        # for each of the keys in divisions, make chronological pages for that
        # directory. (this is sorted so that, for example, "2011" goes before
        # "2011/12". If it weren't sorted, you'd get an error because the
        # directory "2011/12" can't be created before the directory "2011".)
        for directory in sorted(divisions.keys()):
            # get the list of posts
            posts = divisions[directory]
            # get the real directory by prepending the destination_directory
            directory = os.path.join(self.destination_directory, directory)
            # if the directory doesn't exist, create it.
            if not os.path.exists(directory):
                os.mkdir(directory)
            # sort posts by the year, then month, then day, with the most
            # recent first.
            posts.sort(key=attrgetter('year', 'month', 'day'), reverse=True)
            # the number of pages
            number = len(posts) // self.posts_per_page
            # if there are any remainders, add another page for them.
            if number * self.posts_per_page < len(posts):
                number += 1
            # make the pages:
            for n in range(number):
                # if this is the first page, name it "index.html"
                if n == 0:
                    name = os.path.join(directory, "index.html")
                else:
                    name = os.path.join("%s" % directory, "%d.html" % n)
                # if this isn't page 0, previous should link previous page.
                if n == 0:
                    prev = None
                    page_number = 1
                elif n == 1:
                    prev = "index.html"
                    page_number = n + 1
                else:
                    prev = "%d.html" % (n - 1)
                # if this isn't the last, next should link to the next page.
                if n == number - 1:
                    next = None
                else:
                    next = "%d.html" % (n + 1)
                # slice the list of posts according to how many should be on
                # this page
                p = posts[n * self.posts_per_page:(n + 1) *
                            self.posts_per_page]
                interpret(chronological_template, name, posts=p, next=next,
                            previous=prev, total_pages=number, page_number=page_number)
        # for each of the posts, apply the mako template and write it to a
        # file.
        for post in divisions[""]:
            destination = os.path.join(self.destination_directory, post.url)
            # interpret the post
            interpret(post_template, destination, post=post)
        # finally, for each of the templates in the templates/feeds directory,
        # give them the posts.
        feed_dir = os.path.join(self.templates_directory, "feeds")
        if os.path.exists(feed_dir):
            for feed in (os.listdir(feed_dir)):
                # save the output to the name of the file without the
                # last suffix
                destination = os.path.join(self.destination_directory,
                        ".".join(feed.split(".")[:-1]))
                # interpret this template, given the list of posts
                interpret(os.path.join(feed_dir, feed), destination,
                                                    posts=divisions[""])


info = {"class": BlogController}
