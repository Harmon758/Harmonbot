; http://services.runescape.com/m=rswiki/en/Grand_Exchange_APIs
; http://forums.zybez.net/runescape-2007-prices/api/?info
; http://itemdb.biz/

on *:text:!ge*:#:{
  if ($sock(ge)) { sockclose ge }
  if (!$2) {
    msg # Please specify an item.
    return
  }
  set %message msg $chan
  set %ge_item $replace($2-,$chr(32),$chr(43))
  set %ge_item2 $capital($lower($2-))
  set %ge_url /index.php?search= $+ %ge_item
  set %item_id 0
  sockopen ge www.itemdb.biz 80
  timer 1 2 ge
}

alias ge {
  if (%item_id) {
    var %url = http://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json?item= $+ %item_id
    var %price = $json(%url,item,current,price)
    var %name = $json(%url,item,name)
    if (%name) { %message Price of %name $+ : %price gp }
    else { %message Item %ge_item2 not found. Blame itemdb.biz. }
  }
  else { %message Item %ge_item2 not found. Blame itemdb.biz. }
  /*
  else {
    var %category = 0
    while (%category != 37 && !%price) {
      inc %category
      var %url = http://services.runescape.com/m=itemdb_rs/api/catalogue/items.json?category= $+ %category $+ &alpha= $+ $replace($2-,$chr(32),$chr(43)) $+ &page=1
      var %price = $json(%url,items,0,current,price)
    }
    if (%price) {
      var %name = $json(%url,items,0,name)
      %message Price of %name $+ : %price gp
    }
    else { %message Item %ge_item2 not found. }
  }
  */
  return
}

on *:SOCKOPEN:ge: {
  sockwrite -nt $sockname GET %ge_url HTTP/1.1
  sockwrite -nt $sockname Host: www.itemdb.biz
  sockwrite $sockname $crlf
}

on *:SOCKREAD:ge: {
  if (!$sockerr) {
    var %sockreader
    sockread %sockreader
    if (*Your search for* iswm %sockreader) {
      if ($regex(%sockreader,<center><b>([0-9]{0,9})</b></center></td><td style='padding-left:10px;text-align:left;'> $+ %ge_item2 $+ <)) {
        set %item_id $regml(1)
        sockclose ge
      }
      elseif ($regex(%sockreader,<center><b>([0-9]{0,9})</b></center></td><td style='padding-left:10px;text-align:left;'> $+ %ge_item2)) {
        set %item_id $regml(1)
        sockclose ge
      }
      else {
        var %regex_return = $regex(%sockreader,<center><b>(.*?)</b></center>)
        set %item_id $regml(1)
        sockclose ge
      }
    }
    elseif (*Your search returned no results.* iswm %sockreader) {
      set %item_id 0
      sockclose ge
    }
  }
}

on *:text:!zybez*:#:{
  if (!$2) {
    msg # Please specify an item.
    return
  }
  var %url = http://forums.zybez.net/runescape-2007-prices/api/item/ $+ $replace($2-,$chr(32),$chr(43))
  var %price = $json(%url,average)
  var %name = $json(%url,name)
  if (%name) { msg # Average price of %name $+ : %price gp }
  else { msg # Item $2- not found. }
}
