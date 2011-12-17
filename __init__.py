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
        self.contents = s.decode() 

class BlogController(cytoplasm.controllers.Controller):
    def __init__(self, data, destination, templates="_templates", posts_per_page=10):
        # take the base arguments for a controller and, optinally, the number of posts per page.
        self.posts_per_page = posts_per_page
        # pass the base arguments to the base controller's __init__
        cytoplasm.controllers.Controller.__init__(self, data, destination, templates)
        
    def __call__(self):
        # this is a dictionary where the values are lists of Post objects and the keys are the 
        # directories where those posts should go. For example, divisions["2011"] will have all
        # the things posted in 2011. There will be months, too, like divisions["2011/12"]. 
        # Everything will be in divisions[""].
        divisions = defaultdict(list)
        post_template = "%s/%s" %(self.templates_directory, "post.mako")
        chronological_template = "%s/%s" %(self.templates_directory, "chronological.mako")
        for file in os.listdir(self.data_directory):
            # instantiate the Post object
            post = Post("%s/%s" %(self.data_directory, file))
            # append it to the grand list of posts
            divisions[""].append(post)
            # append it to the list of posts for its year and month.
            divisions[str(post.year)].append(post)
            divisions["%d/%d" %(post.year, post.month)].append(post)
        # for each of the keys in divisions, make chronological pages for that directory.
        # (this is sorted so that, for example, "2011" goes before "2011/12". If it weren't sorted,
        # you'd get an error because the directory "2011/12" can't be created before the directory
        # "2011".)
        for directory in sorted(divisions.keys()):
            # get the list of posts
            posts = divisions[directory]
            # get the real directory by prepending the destination_directory
            directory = "%s/%s" %(self.destination_directory, directory)
            # if the directory doesn't exist, create it.
            if not os.path.exists(directory): os.mkdir(directory)
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
        # for each of the posts, apply the mako template and write it to a file.
        for post in divisions[""]:
            destination = "%s/%s" %(self.destination_directory, post.url)
            # interpret the post
            interpret(post_template, destination, post=post)

info = { "class" : BlogController }
