# -*- Coding: utf-8 -*-

import cytoplasm
import os
from operator import attrgetter
from collections import defaultdict
from .posts import Post
from cytoplasm.interpreters import interpret


class BlogController(cytoplasm.controllers.Controller):
    def __init__(self, site, data, destination, templates="_templates",
            posts_per_page=10):
        # take the base arguments for a controller and, optinally, the number
        # of posts per page.
        self.posts_per_page = posts_per_page
        # pass the base arguments to the base controller's __init__
        cytoplasm.controllers.Controller.__init__(self, site, data,
                destination, templates)

    def __call__(self):
        # this is a dictionary where the values are lists of Post objects and
        # the keys are the directories where those posts should go. For
        # example, divisions["2011"] will have all the things posted in 2011.
        # There will be months, too, like divisions["2011/12"].
        # Everything will be in divisions[""].
        divisions = defaultdict(list)
        # create an archive for chronological pages
        # archive keys are years and values are lists of months
        archive = {}
        # figure out the templates to use:
        post_template = self.template("post")
        chronological_template = self.template("chronological")
        for file in os.listdir(self.data_directory):
            # instantiate the Post object
            post = Post(self, os.path.join(self.data_directory, file))
            # append it to the grand list of posts
            divisions[""].append(post)
            # append it to the list of posts for its year and month.
            divisions[str(post.year)].append(post)
            divisions[os.path.join(str(post.year), str(post.month))].append(
                                                                        post)
            # populate archive
            if not post.year in archive:
                archive[post.year] = []
            if not post.month in archive[post.year]:
                archive[post.year].append(post.month)
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
                interpret(chronological_template, name, self.site, posts=p,
                        next=next, previous=prev, total_pages=number,
                        page_number=page_number, archive=archive)
        # for each of the posts, apply the mako template and write it to a
        # file.
        for post in divisions[""]:
            destination = os.path.join(self.destination_directory, post.url)
            # interpret the post
            interpret(post_template, destination, self.site, post=post)
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
                        self.site, posts=divisions[""])


info = {"class": BlogController}
