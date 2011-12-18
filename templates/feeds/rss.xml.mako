<?xml version="1.0" encoding="UTF-8" ?>
<%
    import datetime
    today = datetime.datetime.today()
    timestamp = lambda date: date.strftime("%a, %d %b %Y %H:%M:%S %z")
    # configure these...
    title = "Example Blog"
    url = "http://example.com/blog/"
%>
<rss version="2.0">
<channel>
<title> ${title} </title>
    <description>This is an example of an RSS feed</description>
    <link> ${url} </link>
    <lastBuildDate>${timestamp(today)}</lastBuildDate>
    <pubDate>${timestamp(posts[-1].datetime)}</pubDate>
    <ttl>1800</ttl>

% for post in posts:
    <item>
        <title> ${post.title} </title>
        <link>${url}${post.url}</link>
        <guid>${url}${post.url}</guid>
        <pubDate> ${timestamp(post.datetime)} </pubDate>
        <content:encoded><![CDATA[
${post.contents}
        ]]></content>
    </item>
% endfor
</channel>
</rss>
