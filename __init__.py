import os, cytoplasm, yaml, re
from operator import attrgetter
from collections import defaultdict
from cytoplasm.interpreters import interpret
from cytoplasm.errors import ControllerError

def metadata(file):
    "Read the metadata for file `file` from file.yaml."
    f = open(file, "r")
    contents = f.read()
    f.close()
    # get everything within comments that look like:
    # <!-- metadata
    # -->
    commented = re.sub(r'<!-- metadata\n(.*?)\n-->.*', r'\1', contents, flags=re.DOTALL)
    # if there's no difference between the contents of the file and `commented`, raise an error.
    if commented == contents: 
        raise ControllerError("Post '%s' has no commented metadata." %(file))
    meta = yaml.load(commented)
    # raise an error if there's no title in the metadata
    if "title" not in meta.keys():
        raise ControllerError("Post '%s' doesn't have a title in its metadata." %(file))
    # raise an error if there's no date in the metadata:
    if "date" not in meta.keys():
        raise ControllerError("Post '%s' doesn't have a date in its metadata." %(file))
    return meta

class Post(object):
    "A sort-of file-like object that defines a post."
    def __init__(self, path):
        self.path = path
        self.contents = None
        # get metadata, and update this object's attributes with it. 
        # This allows the user to have arbitrary, custom fields further than "title" and "date".
        self.__dict__.update(metadata(self.path))
        # Get some things from the metadata
        self.year, self.month, self.day = [int(n) for n in self.date.split("/")]
        self.slug = self.title.replace(" ", "-")
        self.url = "%d/%d/%s.html" %(self.year, self.month, self.slug)
        # Interpret the file.
        interpret(self.path, self)

    def close(self):
        # This is just here so that python doesn't throw up an error when something else thinks
        # this is a file.
        pass

    def write(self, s):
        # instead of writing to disk, simply change the contents attribute.
        self.contents = s 

class BlogController(cytoplasm.controllers.Controller):
    def __init__(self, data, destination, templates="_templates", posts_per_page=10):
        # take three arguments: the source directory, the destination directory, and, optionally,
        # a directory wherein the templates reside and a number of posts per page.
        self.templates_directory = templates
        self.posts_per_page = posts_per_page
        cytoplasm.controllers.Controller.__init__(self, data, destination)
        
    def __call__(self):
        posts = []
        years = defaultdict(list)
        months = defaultdict(list)
        post_template = "%s/%s" %(self.templates_directory, "post.mako")
        chronological_template = "%s/%s" %(self.templates_directory, "chronological.mako")
        def chronological(directory, posts):
            # sort posts by the year, then month, then day, with the most recent first.
            posts.sort(key=attrgetter('year', 'month', 'day'), reverse=True)
            # the number of pages
            number = len(posts) // self.posts_per_page
            # if there are any remainders, add another page for them.
            if number * self.posts_per_page < len(posts): number += 1
            # make the pages:
            for n in range(number):
                # if this is the first page, name it "index.html"
                if n == 0: name = "%s/index.html" %(directory)
                else: name = "%s/%d.html" %(directory, n)
                # if this isn't page 0, previous should link to the page before
                if n == 0: prev = None
                elif n == 1: prev = "index.html"
                else: prev = "%d.html" %(directory, n - 1)
                # if this isn't the last page, next should link to the next page...
                if n == number - 1: next = None
                else: next = "%d.html" %(n + 1)
                # slice the list of posts according to how many should be on this page
                p = posts[n * self.posts_per_page:(n + 1) * self.posts_per_page]
                interpret(chronological_template, name, posts=p, next=next, previous=prev)
        
        for post in os.listdir(self.data_directory):
            # instantiate the Post object
            this_post = Post("%s/%s" %(self.data_directory, post))
            # figure out where the final version of this post should go
            destination = "%s/%s" %(self.destination_directory, this_post.url)
            # make the year and month directories, if they don't exist:
            yeardir = "%s/%d" %(self.destination_directory, this_post.year)
            if not os.path.exists(yeardir): os.mkdir(yeardir)
            monthdir = "%s/%d/%d" %(self.destination_directory, this_post.year, this_post.month)
            if not os.path.exists(monthdir): os.mkdir(monthdir)
            # interpret the post
            interpret(post_template, destination, post=this_post)
            # append it to the grand list of posts
            posts.append(this_post)
            # append it to the lists for each year and month
            years[this_post.year].append(this_post)
            months["%d/%d" %(this_post.year, this_post.month)].append(this_post)
        # make the base chronological pages
        chronological(self.destination_directory, posts)
        # make chronological pages for each year...
        for year in years.keys(): 
            chronological("%s/%d" %(self.destination_directory, year), years[year])
        # and for each month
        for month in months.keys(): 
            chronological("%s/%s" %(self.destination_directory, month), months[month])

info = { "class" : BlogController }
