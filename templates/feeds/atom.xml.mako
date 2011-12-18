<?xml version="1.0" encoding="UTF-8" ?>
<%
    import datetime
    today = datetime.date.today()
    today = datetime.datetime(today.year, today.month, today.day)
    def isoformat(date):
        if date.tzname() == None:
            return today.isoformat() + "Z"
        else:
            return today.isoformat() 
    # configure these...
    title = "Example Blog"
    url = "http://example.com/blog"
%>
<feed xmlns="http://www.w3.org/2005/Atom">
    <id>${url}</id>
    <title> ${title} </title>
    <link href="${url}/atom.xml" rel="self" />
    <link href="${url}" />
    <updated>${isoformat(today)}</updated>
% for post in posts:
    <entry>
        <title>${post.title}</title>
    % if post.author != None:
        <author>
            <name>${post.author}</name>
        % if post.email != None:
            <email>${post.email}</email>
        % endif 
        </author>
    % endif
        <link href="${url}${post.url}" type="text/html" />
        <id>${url}${post.url}</id>
        <updated>${isoformat(post.datetime)}</updated>
        <content type="html"><![CDATA[
${post.contents}
    ]]></content>
    </entry>
% endfor
</feed>




