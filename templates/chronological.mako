## This is for pages like the index page of a blog, i.e. ones where multiple posts are displayed.
## It should be passed a list of Post objects
<%page args="posts"/>
% for post in posts
${post.title}
<br>
${post.contents}
<hr>
% endfor
