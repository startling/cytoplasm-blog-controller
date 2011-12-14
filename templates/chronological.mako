## This is for pages like the index page of a blog, i.e. ones where multiple posts are displayed.
## It should be passed a list of Post objects and the urls of the next and previous pages, if any.
<%page args="posts, previous=None, next=None"/>
% for post in posts:
${post.title}
<br>
${post.contents}
<hr>
% endfor
% if previous != None:
<a href="${previous}">previous page</a> 
% endif
% if next != None:
<a href="${next}">next page.</a>
% endif
