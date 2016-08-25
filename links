
; ***REMOVED***
; links/api's
;
;https://www.googleapis.com/youtube/v3/videos?id=VIDEOID&key=***REMOVED***&part=snippet,contentDetails,statistics
;***REMOVED***
;***REMOVED***

on *:text:youtube*:#: {
  if ($nick isop # || $nick == harmon758) && ($2) {
    if ($2 == on) {
      set %youtube.status. $+ $chan on
      msg # Youtube link detection is on.
      return
    }
    if ($2 == off) {
      set %youtube.status. $+ $chan off
      msg # Youtube link detection is off.
      return
    }
  }
}

on *:text:!youtubeinfo*:#: {
  noop $regex($strip($2),.*youtube.*\/watch\?v=(.{11})&?.*)
  var %videoid = $regml(1)
  var %url = https://www.googleapis.com/youtube/v3/videos?id= $+ %videoid $+ &key=***REMOVED***&part=snippet,contentDetails,statistics
  if ($json(%url,pageInfo,totalResults)) {
    var %title = $json(%url,items,0,snippet,title)
    noop $regex($json(%url,items,0,contentDetails,duration),P([0-9]*Y)?([0-9]*M)?([0-9]*W)?([0-9]*D)?T([0-9]*H)?([0-9]*M)?([0-9]*S))
    var %counter = $regml(0)
    var %length
    while (%counter != 0) {
      %length = $lower($regml(%counter)) %length
      dec %counter
    }
    var %likes = $json(%url,items,0,statistics,likeCount)
    var %dislikes = $json(%url,items,0,statistics,dislikeCount)
    var %likepercentage = $round($calc(%likes / (%likes + %dislikes) * 100), 2)
    %likes = $bytes(%likes,bd)
    %dislikes = $bytes(%dislikes,bd)
    var %views = $bytes($json(%url,items,0,statistics,viewCount),bd)
    var %channel = $json(%url,items,0,snippet,channelTitle)
    noop $regex($strip($json(%url,items,0,snippet,publishedAt)),(.*)T.*)
    var %published = $regml(1)
    msg # ( $+ $capital($nick) $+ ) %title $chr(124) Length: %length $chr(124) Likes: %likes $+ , Dislikes: %dislikes ( $+ %likepercentage $+ $chr(37) $+ ) $chr(124) Views: %views $chr(124) %channel on %published
  }
  else { msg # ( $+ $capital($nick) $+ ) Video not found. }
}

on *:text:*youtube.com/watch?v=*:#: {
  if (%youtube.status. [ $+ [ $chan ] ] == off) { return }
  noop $regex($strip($1-),.*youtube.*\/watch\?v=(.{11})&?.*)
  var %videoid = $regml(1)
  var %url = https://www.googleapis.com/youtube/v3/videos?id= $+ %videoid $+ &key=***REMOVED***&part=snippet,contentDetails,statistics
  if ($json(%url,pageInfo,totalResults)) {
    var %title = $json(%url,items,0,snippet,title)
    noop $regex($json(%url,items,0,contentDetails,duration),P([0-9]*Y)?([0-9]*M)?([0-9]*W)?([0-9]*D)?T([0-9]*H)?([0-9]*M)?([0-9]*S))
    var %counter = $regml(0)
    var %length
    while (%counter != 0) {
      %length = $lower($regml(%counter)) %length
      dec %counter
    }
    var %likes = $json(%url,items,0,statistics,likeCount)
    var %dislikes = $json(%url,items,0,statistics,dislikeCount)
    var %likepercentage = $round($calc(%likes / (%likes + %dislikes) * 100), 2)
    %likes = $bytes(%likes,bd)
    %dislikes = $bytes(%dislikes,bd)
    var %views = $bytes($json(%url,items,0,statistics,viewCount),bd)
    var %channel = $json(%url,items,0,snippet,channelTitle)
    noop $regex($strip($json(%url,items,0,snippet,publishedAt)),(.*)T.*)
    var %published = $regml(1)
    msg # ( $+ $capital($nick) $+ ) %title $chr(124) Length: %length $chr(124) Likes: %likes $+ , Dislikes: %dislikes ( $+ %likepercentage $+ $chr(37) $+ ) $chr(124) Views: %views $chr(124) %channel on %published
  }
  else { msg # ( $+ $capital($nick) $+ ) Video not found. }
}

on *:text:!longurl*:#: {
  if ($nick isop #) && ($2) {
    var %url = http://api.longurl.org/v2/expand?url= $+ $2 $+ &title=1&format=json
    if ($json(%url, title)) { msg # $json(%url, title) $+ : $json(%url, long-url) }
    else { msg # $json(%url, long-url) }
  }
}

on *:text:!translate*:#: {
  var %url = https://translate.yandex.net/api/v1.5/tr.json/translate?key=***REMOVED***&lang=en&text= $+ $2-
  msg # $json(%url, text, 0)
}

on *:text:!news*:#: {
  if ($nick isop # || $nick == harmon758) && ($2) {
    if ($2 == on) {
      set %!news.status. $+ $chan on
      msg # !news is on.
      return
    }
    if ($2 == off) {
      set %!news.status. $+ $chan off
      msg # !news is off.
      return
    }
  }
  if (%!news.status. [ $+ [ $chan ] ] == off) { return }
  if (!$2) { msg # $capital($nick) $+ , please enter a search parameter. | return }
  var %url = https://ajax.googleapis.com/ajax/services/search/news?v=1.0&q= $2-
  var %results = $json(%url, responseData, results, 0)
  if (%results) {
    var %content
    noop $regsub($json(%url, responseData, results, 0, content),/(<[^>]+>)/g, $null, %content)
    var %unescapedurl = $json(%url, responseData, results, 0, unescapedUrl)
    var %title = $json(%url, responseData, results, 0, titleNoFormatting)
    var %publisher = $json(%url, responseData, results, 0, publisher)
    var %date = $json(%url, responseData, results, 0, publishedDate)
    msg # ( $+ $capital($nick) $+ ) %title $+ : %content
    msg # %publisher on %date $chr(124) %unescapedurl
  }
  else { msg # ( $+ $capital($nick) $+ ) No news results found. }
}

on *:text:links*:#: {
  if ($nick isop # || $nick == harmon758) && ($2) {
    if ($2 == on) {
      set %links.status. $+ $chan on
      msg # Link detection is on.
      return
    }
    if ($2 == off) {
      set %links.status. $+ $chan off
      msg # Link detection is off.
      return
    }
  }
}

on *:text:*http*:#: {
  if (%links.status. [ $+ [ $chan ] ] == off) { return }
  if ($nick == nightbot) { return }
  if (gyazo isin $1-) { return }
  var %text = $1-
  var %words = $numtok(%text, 32)
  var %counter = 1
  while (%counter <= %words) {
    if ($regex($gettok(%text, %counter, 32),.*https?:\/\/(.*))) {
      var %url = http://decenturl.com/api-title?u= $+ $regml(1)
      var %title = $json(%url, 1)
      if (%title) { msg # ( $+ $capital($nick) $+ ) Title: %title }
    }
    inc %counter
  }
}

;---

on *:text:!twitterapitest:#: { 
  sockclose twitterapi
  set %twitterapi.channel $chan
  sockopen -e twitterapi api.twitter.com 443
}

on *:SOCKOPEN:twitterapi: {
  sockwrite -n $sockname GET /1.1/statuses/show.json?id=646753423136677890 HTTP/1.1
  sockwrite -n $sockname Host: api.twitter.com
  sockwrite -n $sockname Authorization: Bearer ***REMOVED***
  sockwrite -n $sockname $crlf
}

on *:SOCKREAD:twitterapi: {
  if (!$sockerr) {
    while (1) {
      var %temp
      sockread %temp
      echo -ag sockread: %temp
      if ($sockbr == 0) {
        echo -ag sockread: %temp
        echo -ag $sock($sockname).rq
        sockclose twitterapi
        return
      }
    }
  }
}

on *:sockclose:twitterapi: {
  if (!$sockerr) {
    var %a
    sockread -f %a
    if ($sockbr == 0) return
    echo -a > %a
  }
}

/*
on *:text:!twitterapitest:#: { 
  sockclose twitterapi
  set %twitterapi.channel $chan
  sockopen -e twitterapi api.twitter.com 443
}

on *:SOCKOPEN:twitterapi: {
  sockwrite -n $sockname POST /oauth2/token HTTP/1.1
  sockwrite -n $sockname Host: api.twitter.com
  sockwrite -n $sockname Authorization: Basic ***REMOVED***
  sockwrite -n $sockname Content-Type: application/x-www-form-urlencoded;charset=UTF-8
  sockwrite -n $sockname Content-Length: 29
  sockwrite -n $sockname
  sockwrite $sockname grant_type=client_credentials
}

on *:SOCKREAD:twitterapi: {
  if (!$sockerr) {
    while (1) {
      var %temp
      sockread %temp
      if (*bearer* iswm %temp) {
        echo -ag sockread: %temp
        sockclose twitterapi
        return
      }
    }
  }
}

on *:sockclose:twitterapi: {
  if (!$sockerr) {
    var %a
    sockread -f %a
    if ($sockbr == 0) return
    echo -a > %a
  }
}
*/
