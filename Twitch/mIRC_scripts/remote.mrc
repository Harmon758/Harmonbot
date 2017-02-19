; ***REMOVED***
; 
; Also Checks For "rip ge", "rip grand exchange", "rip wildy", "raf2*com", "rip pvp"
; "happy bday", "happy birthday"
; -----Files and Commands-----
; --remote.ini--
; !commands !additionalcommands1 !additionalcommands2 !mikkiscapecommands !imagrillcommands
; !07rswiki !averagefps !bye !cache !calc !followers !google !grats !gz !hello !highfive !hi !hug !imfeelinglucky !indecentcodehs 
; !level !lmgtfy !mods !noob !poke !randomviewer !remindcache !remindwarbands !reset !rng !rswiki !rswiki07 !timer !title !viewers !warbands !wiki !xpat !xpbetween
; --changelog--
; --whatis--
; !whatis
; --mikkiscapecommands--
; !99rc !bday !caught !clan !cml !con !emotes !fish !fletch !glory !links !mine !mining !mikki !mikkitime !music !pi !pouch
; !pray !rc !repair !rotation !runecrafting !runetracker !skype !slay !spotify !stats !subscribe !thief !thieving !tick !totalxp
; also checks for "alt", "3 accounts", "3 accs", "three accounts", "three accs"
; --imagrillcommands--
; !altstats !arts !artsdictionary !artsdictionary2 !artstime !aus !blue !catonhead !cats !caught !death !dream !dwarf !ed8 !edate !fail !fortune !googer !hair !humage !modabuse
; !moo !muted !omg !p !pets !pudding !re;birth1 !rebirth1 !save !sick !sneeze !soab !troll !tutorial !week
; also checks for ":|", "-.-", ":3", "!addcom !h harmo pls", ":p", "banana", "failfish", "lick it", "yawn"
; --miscellaneous--
; !120 !122 !asylum !cheese !christmas !gj !guthixiancache !harmon !harmonbot !help !hobgobmike 
; !indecent !illuminati !ironman !justdoit !lag !life !love !kitty !nightbot !no !nudes !puppy !tns !zezima
; --weather--
; !alert !alertinfo !alerts !alertsinfo !almanac !current !forecast !forecast[1-10] !time !weather
; --ehp--
; !ehp
; --unitconversions--
; !ctof !ftoc !lbtokg !kgtolb !fttom !mtoft !fitom !mtofi !gtooz !oztog !mitokm !kmtomi !ozttog !gtoozt !ozttooz !oztoozt
; --roulette--
; !roulette
; --rps--
; !rps
; --hiscores--
; !hiscore(s) !highscore(s)
; --ge--
; !ge !zybez
; --monster--
; !monster
; --adventure--
; !adventure
; --define--
; !audiodefine !define !randomword
; ----------------------------
;

on *:text:!documentation*:#:{ msg # My Documentation: https://docs.google.com/document/d/1tsGQ-JAZiW-Y2sLQbd1UG441dhZhNtLmzFXx936YG08/ }
on *:text:!commands*:#:{ msg # My current commands are !additionalcommands[1-2] !adventure !averagefps !calc ![streamer]commands !followed !followers !google $&
  !noob !randomviewer !rscommands !time !timer !uptime !weather !whatis !wiki Also see !documentation }
on *:text:!additionalcommands1*:#:{ msg # Some additional miscellaneous commands (1/2): !bye !commands !current !forecast !forecast[1-10] $&
  !grats !hello !highfive !imfeelinglucky !lmgtfy !mods !nightbot !poke !rng !roulette !rps !title !tns !unitconversions !viewers }
on *:text:!additionalcommands2*:#:{ msg # Some additional miscellaneous commands (2/2): !alert !alertinfo !alerts !alertsinfo !almanac !asylum !cheese !christmas $&
  !gj !gz !harmon !harmonbot !help !hi !hobgobmike !hug !illuminati !ironman !justdoit !lag !life !love !kitty !no !nudes !puppy !zezima }
on *:text:!rscommands*:#:{ msg # My Runescape commands: !07rswiki !120 !122 !cache !ehp !ge !guthixiancache !highscores !hiscores !indecent !indecentcodehs $&
  !level !monster !remindcache !remindwarbands !reset !rswiki !rswiki07 !warbands !xpat !xpbetween !zybez }
on *:text:!unitconversions*:#:{ msg # !ctof !ftoc !lbtokg !kgtolb !fttom !mtoft !fitom !mtofi !gtooz !oztog !mitokm !kmtomi !ozttog !gtoozt !ozttooz !oztoozt }
;on *:text:!aribeeecommands*:#:{ msg # !aritime !name !rabbit !redeem !socialclub }
on *:text:!mikkiscapecommands*:#:{ msg # !99rc !bday !caught !clan !cml !emotes !glory !links !mikki !mikkitime !music !pi !pouch $&
  !repair !rotation !runetracker !skype !spotify !stats !subscribe !tick }
on *:text:!imagrillcommands*:#:{ msg # !altstats !arts !artsdictionary !artsdictionary2 !artstime !aus !blue !catonhead !cats !caught !death !dream  !ed8 !edate !fail !fortune $&
  !googer !hair !humage !modabuse !moo !muted !omg !p !pets !pudding !re;birth1 !rebirth1 !save !sick !sneeze !soab !troll !tutorial !week }
;
; https://api.twitch.tv/kraken/channels/[streamer]/follows
; https://api.twitch.tv/kraken/streams/[streamer]
; weather underground api
; dictionary api
;
; TO DO
;
; add lots of documentation - update !whatis
; organize
; look into !editcom?
; add to !whatis
; find editor, tester, IDE
; add different stat commands
; upgrade/fix !calc - add pi, check errors, fix - /0, pi, 56%3 = 0, ^ ?, ! ?, % support, add wolframalpha, d(dx)[3x]
; attack thecatbot
; !level error message
; add other unit conversions
; expand !3accs - 3 dif accs
; clean up/upgrade !xpbetween
; add goals
; standardize bday
; add rs hiscores
; add big chin
; !ehp clean up/upgrade
; command count?
; change !xpat?
; show one weather option
; add random to other commands
; test all commands
;
; elemental symbols - fe
; ideas
; user interaction
;
; look accounts up
;
; note: similar commands, before first; ideas passed on
;
; update changelog, to do
;

on $*:text:/.*(N l G G E R|Time me out no balls|jagexpromotions|rip ge|rip grand exchange|rip osrs|rip wildy|weblogin|raf2\*com|rip pvp|runescape\.com\.al|runescape\.com\.rsforum\.cu\.cc|service-runescape\.cf|runescape\.gq|runescape\.ga|runescape\.com\.de|goo.gl\/vlMhdF)/Si:#:{ msg # /timeout $nick 2 }

on $*:text:/.*(happy bday|happy birthday)/Si:#:{ msg # Happy Birthday! }
; on *:text:!bday*:#:{ msg # Happy Birthday! }

; on *:text:!07pc*:#:{ msg # $json(%json.enc(http://forums.zybez.net/runescape-2007-prices/api/rune+axe),average) }
/*
on *:text:!calc*:#:{
  if ($2 isnum && $4 isnum && ($3 == + || $3 == - || $3 == * || $3 == / || $3 == ^ || $3 == %)) {
    msg # $calc($2-)
  }
  else { msg # Invalid Operation. }
}
*/

;-----
on $*:text:/^[!](07rswiki|rswiki07)/Si:#:{ msg # $rswiki07($2-) }
on *:text:!averagefps*:#:{
  var %url = https://api.twitch.tv/kraken/streams/ $+ $mid($chan,2-) $+ ?client_id=***REMOVED***
  var %fps = $json(%url,stream,average_fps)
  if (%fps) { msg # Average FPS: %fps }
  else { msg # Average FPS not found. }
}
on *:text:!bye*:#:{
  if (!$2 || $2- == harmonbot) { msg # Bye, $capital($nick) $+ ! }
  else { msg # $capital($2-) $+ , $capital($nick) says goodbye! }
}
on *:text:!cache*:#:{
  var %timeleft = $timeleft(0, 10800)
  if (%timeleft isnum 0-) msg # $my_duration(%timeleft) until Guthixian Cache.
}
on *:text:!calc*:#: msg # $iif($regsubex($remove($2-,$chr(32),$chr(44)),/((^|[+-/^*%]+)(([0-9]|\56)+)(k|m|b)|(^|[+-/^*%]+)(([0-9]|\56)+)|(^|[+-/^*%]+)(\50(.+?)\51))/ig,),Syntax Error,$iif(!$2,Syntax Error,$2- = $regsubex($ticks,$calc($regsubex($ticks,$remove($2-,$chr(44),$chr(32)),/(^|[+-/*%]+|[+-/*%]+\50)(([0-9]|\56)+)(k|m|b)/ig,\1 $+ ( $+ \2 $+ $iif(\4 == b,*1000000000,$iif(\4 == m,*1000000,*1000)) $+ ))),/\G([+-]?\d+?)(?=(?:\d{3})++(?=\.\d++$|$))/g,\1 $+ $chr(44)))) 
on *:text:!followers*:#:{
  var %url = https://api.twitch.tv/kraken/channels/ $+ $mid($chan,2-) $+ /follows $+ ?client_id=***REMOVED***
  var %followercount = $json(%url,_total)
  msg # There are currently %followercount people following $capital($mid($chan,2-)) $+ .
}
;fix
on $*:text:/^[!](followed|followage|howlong)/Si:#:{
  var %url = https://api.twitch.tv/kraken/users/ $+ $nick $+ /follows/channels/ $+ $mid($chan,2-) $+ ?client_id=***REMOVED***
  var %date = $json(%url,created_at)
  if ($mid(%date,6,2) == 01) { var %month = January }
  elseif ($mid(%date,6,2) == 02) { var %month = Feburary }
  elseif ($mid(%date,6,2) == 03) { var %month = March }
  elseif ($mid(%date,6,2) == 04) { var %month = April }
  elseif ($mid(%date,6,2) == 05) { var %month = May }
  elseif ($mid(%date,6,2) == 06) { var %month = June }
  elseif ($mid(%date,6,2) == 07) { var %month = July }
  elseif ($mid(%date,6,2) == 08) { var %month = August }
  elseif ($mid(%date,6,2) == 09) { var %month = September }
  elseif ($mid(%date,6,2) == 10) { var %month = October }
  elseif ($mid(%date,6,2) == 11) { var %month = November }
  elseif ($mid(%date,6,2) == 12) { var %month = December }
  if ($mid(%date,9,1) == 0) { var %day = $mid(%date,10,1) }
  else { var %day = $mid(%date,9,2) }
  if (%date) { msg # $capital($nick) followed on %month %day $mid(%date,1,4) $+ , $my_duration($calc($ctime - $ctime($mid(%date,1,10) $mid(%date,12,8))) + 21600) ago. }
  else { msg # $capital($nick) $+ , you haven't followed yet! }
}
on *:text:!google*:#: { msg # google.com/search?q= $+ $replace($2-,$chr(32),$chr(43)) }
on $*:text:/^[!](grats|gz)/Si:#:{
  if ($2) { msg # Congratulations, $capital($2-) $+ !!!!! }
  else { msg # Congratulations!!!!! }
}
on *:text:!hello*:#:{
  if (!$2 || $2- == harmonbot) { msg # Hello, $capital($nick) $+ ! }
  else { msg # $capital($2-) $+ , $capital($nick) says hello! }
}
on *:text:!highfive*:#:{ 
  if ($2 == random) { msg # $capital($nick) highfives $randomviewer $+ ! }
  elseif ($2 == $nick) { msg # $capital($nick) highfives themselves $+ . o_O }
  elseif ($2 == harmonbot) { msg # !highfive $capital($nick) }
  elseif ($2) { msg # $capital($nick) highfives $capital($2-) $+ ! }
  else { msg # $capital($nick) highfives no one $+ . :-/ }
}
on *:text:!hi*:#:{
  if ($1 == !hiscores || $1 == !hiscore || $1 == !highscore || $1 == !highscores) { return }
  if (!$2 || $2- == harmonbot) { msg # Hello, $capital($nick) $+ ! }
  else { msg # $capital($2-) $+ , $capital($nick) says hello! }
}
on *:text:!hug*:#:{
  if ($2 == random) { msg # $capital($nick) hugs $randomviewer $+ ! }
  elseif ($2 == $nick) { msg # $capital($nick) hugs themselves $+ . o_O }
  elseif ($2 == harmonbot) { msg # !hug $capital($nick) }
  elseif ($2) { msg # $capital($nick) hugs $capital($2-) $+ ! }
  else { msg # $capital($nick) hugs $capital($nick) $+ . o_O }
}
on *:text:!imfeelinglucky*:#: { msg # google.com/search?btnI&q= $+ $replace($2-,$chr(32),$chr(43)) }
on *:text:!indecentcodehs*:#:{ msg # indecentcode.com/hs/index.php?id= $+ $replace($2-,$chr(32),$chr(43)) }
on *:text:!level*:#:{
  if (!$2) { msg # Please enter a level. }
  elseif ($2 isnum && $2 >= 1 && $2 < 127) {
    var %2 = $floor($2)
    var %level = 1
    var %xp = 0
    while (%level != %2) {
      %xp = $calc(%xp + $floor($calc(%level + 300 * 2 ^ (%level / 7))))
      inc %level
    }
    %xp = $floor($calc(%xp / 4))
    msg # Runescape Level %2 = $bytes(%xp,bd) xp
  }
  elseif ($2 isnum && $2 > 9000) { msg # It's over 9000! }
  elseif ($2 isnum && $2 == 9000) { msg # Almost there. }
  elseif ($2 isnum && $2 > 126 && $2 < 9000) { msg # I was gonna calculate xp at Level $2. Then I took an arrow to the knee. }
  else { msg # Level $2- does not exist or there is a syntax error. }
}
on *:text:!lmgtfy*:#: { msg # lmgtfy.com/?q= $+ $replace($2-,$chr(32),$chr(43)) }
on *:text:!mods*:#:{
  var %t = 0
  while (%t <= $nick(#,0,o)) {
    var %tmod = $iif(%tmod,%tmod $capital($nick(#,%t,o)),$capital($nick(#,%t,o)))
    inc %t
  }
  msg # Mods Online: $iif(%tmod,%tmod,None)
}
on *:text:!noob*:#:{
  if ($2) {
    if ($count($remove($2-,+,-,_,$chr(32)), harmonbot) != 0) { msg # I am not a noob. }
    elseif ($count($remove($2-,+,-,_,$chr(32)), harmon758) != 0 || $count($remove($2-,+,-,_,$chr(32)), harmon) != 0 || $count($remove($2-,+,-,_,$chr(32)), my creator) != 0 || $count($remove($2-,+,-,_,$chr(32)), my owner) != 0 || $count($remove($2-,+,-,_,$chr(32)), who created me) != 0 || $count($remove($2-,+,-,_,$chr(32)), who made me) != 0 || $count($remove($2-,+,-,_,$chr(32)), 758) != 0 || $count($remove($2-,+,-,_,$chr(32)), nomrah) != 0 || $count($remove($2-,+,-,_,$chr(32)), harmo) != 0) { msg # Harmon is not a noob. }
    elseif ($count($remove($2-,+,-,_,$chr(32)), thisstreamer) != 0 || $count($remove($2-,+,-,_,$chr(32)), thisbroadcaster) != 0) { msg # $capital($mid($chan,2-)) is not a noob. How dare you. }
    elseif ($count($remove($2-,+,-,_,$chr(32)), mikkiscape) != 0 || $count($remove($2-,+,-,_,$chr(32)), mikki) != 0 || $count($remove($2-,+,-,_,$chr(32)), mikhala) != 0) { msg # Mikki is not a noob. How dare you. }
    elseif ($count($remove($2-,+,-,_,$chr(32)), imagrill) != 0 || $count($remove($2-,+,-,_,$chr(32)), arts) != 0 || $count($remove($2-,+,-,_,$chr(32)), sarah) != 0) { msg # Arts is not a noob. How dare you. }
    elseif ($2 == i) { msg # $capital($nick) $+ , you are a noob. }
    elseif ($count($2-, /) != 0 || $count($2-, Ϻ) != 0 || $count($2-, ᴹ) != 0 || $count($2-, ᴵ) != 0 || $count($2-, ᴷ) != 0 || $count($2-, Μ) != 0 || $count($2-, Ι) != 0 || $count($2-, Κ) != 0 $&
      || $count($2-, Η) != 0 || $count($2-, ⁪) != 0) { msg # $capital($nick) $+ , no special characters, you noob. Reported. }
    elseif ($nick == sathonscape) { msg # Sathonscape is a noob. }
    else { msg # $capital($2-) is a noob. }
  }
  else { msg # $capital($nick) $+ , you are a noob. }
}
on *:text:!poke*:#:{
  if ($nick isop #) && ($2) {
    if ($istok(on,$2,32)) {
      set %!poke.status on 
      msg # !poke is on.
      return
    }
    if ($istok(off,$2,32)) {
      set %!poke.status off 
      msg # !poke is off.
      return
    }
  }
  if (%!poke.status == off) { return }
  else {
    if ($2 == random) { msg # $capital($nick) pokes $randomviewer $+ ! }
    elseif ($2 == $nick) { msg # $capital($nick) pokes themselves $+ . o_O }
    elseif ($2 == harmonbot) { msg # !poke $capital($nick) }
    elseif ($2) { msg # $capital($nick) pokes $capital($2-) $+ ! }
    else { msg # $capital($nick) pokes no one $+ . o_O }
  }
}
on *:text:!randomviewer*:#:{ noop $on/off($1, $2, !randomviewer, $randomviewer) }
on *:text:!remindcache*:#:{
  var %timeleft = $timeleft(0, 10800)
  if ($2 isnum 1-179) {
    var %offset = $calc($2 * 60), %msgtime = $calc(%timeleft - %offset)
    msg # $capital($nick) $+ , I'll remind you $my_duration(%offset) before Guthixian Cache.
    if (%msgtime isnum 0-) .timer 1 %msgtime msg # $capital($nick) $+ , Guthixian Cache is in $my_duration(%offset) $+ !
  }
  elseif ($2 <= 0 || $2 >= 180) { msg # $capital($nick) $+ , that is not a valid option for a reminder. Guthixian Cache is every 3 hours. }
  else {
    var %offset = 300, %msgtime = $calc(%timeleft - %offset)
    msg # $capital($nick) $+ , I'll remind you 5 minutes before Guthixian Cache.
    if (%msgtime isnum 0-) .timer 1 %msgtime msg # $capital($nick) $+ , Guthixian Cache is in 5 minutes!
  }
}
on *:text:!remindwarbands*:#:{
  var %timeleft = $timeleft(0, 25200)
  if ($2 isnum 1-419) {
    var %offset = $calc($2 * 60), %msgtime = $calc(%timeleft - %offset)
    msg # $capital($nick) $+ , I'll remind you $my_duration(%offset) before Warbands.
    if (%msgtime isnum 0-) .timer 1 %msgtime msg # $capital($nick) $+ , Warbands is in $my_duration(%offset) $+ !
  }
  elseif ($2 <= 0 || $2 >= 420) { msg # $capital($nick) $+ , that is not a valid option for a reminder. Warbands is every 7 hours. }
  else {
    var %offset = 300, %msgtime = $calc(%timeleft - %offset)
    msg # $capital($nick) $+ , I'll remind you 5 minutes before Warbands.
    if (%msgtime isnum 0-) .timer 1 %msgtime msg # $capital($nick) $+ , Warbands is in 5 minutes!
  }
}
on *:text:!reset*:#:{
  var %timeleft = $timeleft(0, 86400)
  if (%timeleft isnum 0-) msg # $my_duration(%timeleft) until reset.
}
on *:text:!rng*:#: {
  if ($2 isnum) { msg # $rand(1,$2) }
  else { msg # $rand(1,10) }
}
on *:text:!rswiki*:#:{ msg # $rswiki($2-) }
on *:text:!test*:#:{ msg # Hello, World! }
on *:text:!timer*:#:{
  if ($nick isop # || $nick == harmon758) {
    if ($2 isnum) {
      msg # $capital($nick) $+ , a timer has been set for $my_duration($2 * 60).
      .timer 1 $calc(60 * $2) msg # $capital($nick) $+ , it's been $my_duration($2 * 60)!
    }
    else {
      msg # $capital($nick) $+ , a timer has been set for 5 minutes.
      .timer 1 300 msg # $capital($nick) $+ , it's been 5 minutes!
    }
  }
}
on *:text:!title*:#:{
  var %url = https://api.twitch.tv/kraken/streams/ $+ $mid($chan,2-) $+ ?client_id=***REMOVED***
  var %title = $json(%url,stream,channel,status)
  msg # %title
}
on *:text:!viewers*:#:{
  var %url = https://api.twitch.tv/kraken/streams/ $+ $mid($chan,2-) $+ ?client_id=***REMOVED***
  var %viewer_count = $json(%url,stream,viewers)
  var %stream = $json(%url,stream)
  if (%viewer_count) { msg # %viewer_count viewers watching now. }
  elseif (!%stream) { msg # Stream is offline. }
  else { msg # No one is watching right now :-/ }
}
on *:text:!warbands*:#:{
  var %timeleft = $timeleft(0, 25200)
  if (%timeleft isnum 0-) msg # $my_duration(%timeleft) until Warbands.
}
on *:text:!wiki*:#: { msg # $wiki($2-) }
on *:text:!xpat*:#:{
  var %2 = $remove($2,$chr(44))
  if (!$2) { msg # Please enter xp. }
  elseif (%2 isnum && %2 >= 0 && %2 < 200000001) {
    var %2 = $floor(%2)
    var %level = 1
    var %xp = 0
    while (%2 >= %xp) {
      %xp = $calc(%xp * 4)
      %xp = $calc(%xp + $floor($calc(%level + 300 * 2 ^ (%level / 7))))
      %xp = $calc(%xp / 4)
      inc %level
    }
    %level = %level - 1
    msg # $bytes(%2,bd) xp = level %level
  }
  elseif (%2 isnum) { msg # You can't have that much xp! }
  else { msg # Syntax error. }
}
on *:text:!xpbetween*:#:{
  if ($2 isnum && $2 >= 1 && $2 < 127 && $3 isnum && $3 >= 1 && $3 < 127 && $2 < $3) {
    var %2 = $floor($2)
    var %3 = $floor($3)
    var %level = 1
    var %xp = 0
    var %startxp = 0
    var %betweenxp = 0
    while (%level != %3) {
      %xp = $calc(%xp + $floor($calc(%level + 300 * 2 ^ (%level / 7))))
      inc %level
      if (%level == %2) { %startxp = $floor($calc(%xp / 4)) }
    }
    %betweenxp = $calc($floor($calc(%xp / 4)) - %startxp)
    msg # $bytes(%betweenxp,bd) xp between level %2 and level %3
  }
  else { msg # Syntax error. }
}
;-----

;on *:text:!uptime*:#:{
;  set %channel $chan
;  sockclose uptime
;  sockopen uptime nightdev.com 80
;}
on *:sockopen:uptime:{
  if ($sockerr) { sockclose $sockname | halt }
  sockwrite -n $sockname GET /hosted/uptime.php?channel= $+ $mid(%channel,2-) HTTP/1.1
  sockwrite -n $sockname Host: nightdev.com $crlf $+ $crlf
}
on *:sockread:uptime:{
  if ($sockerr) { sockclose $sockname }
  var %streamodata
  sockread %streamodata
  if ($regex(%streamodata,(.*)minutes)) { msg %channel $regml(1) minutes }
  if ($regex(%streamodata,(.*)live.)) { msg %channel $capital($mid(%channel,2-)) is offline. }
}

alias timeleft {
  var %start = $1, %interval = $2, %timeleft
  if ($ctime <= %start) || (!%interval) { %timeleft = $calc(%start - $ctime) }
  else { %timeleft = $calc(%interval - ($ctime - %start) % %interval) }
  return %timeleft
}

alias my_duration {
  var %secs = $1, %my_duration
  if (%secs > 31536000) {
    %my_duration = %my_duration $floor($calc(%secs / 31536000)) year
    if ($floor($calc(%secs / 31536000)) > 1) { %my_duration = %my_duration $+ s }
    %secs = $calc(%secs - $floor($calc(%secs / 31536000)) * 31536000)
  }
  if (%secs > 604800) {
    %my_duration = %my_duration $floor($calc(%secs / 604800)) week
    if ($floor($calc(%secs / 604800)) > 1) { %my_duration = %my_duration $+ s }
    %secs = $calc(%secs - $floor($calc(%secs / 604800)) * 604800)
  }
  if (%secs > 86400) {
    %my_duration = %my_duration $floor($calc(%secs / 86400)) day
    if ($floor($calc(%secs / 86400)) > 1) { %my_duration = %my_duration $+ s }
    %secs = $calc(%secs - $floor($calc(%secs / 86400)) * 86400)
  }
  if (%secs > 3600) {
    %my_duration = %my_duration $floor($calc(%secs / 3600)) hour
    if ($floor($calc(%secs / 3600)) > 1) { %my_duration = %my_duration $+ s }
    %secs = $calc(%secs - $floor($calc(%secs / 3600)) * 3600)
  }
  if (%secs > 60) {
    %my_duration = %my_duration $floor($calc(%secs / 60)) minute
    if ($floor($calc(%secs / 60)) > 1) { %my_duration = %my_duration $+ s }
    %secs = $calc(%secs - $floor($calc(%secs / 60)) * 60)
  }
  if (%secs != 0) {
    %my_duration = %my_duration %secs second
    if (%secs > 1) { %my_duration = %my_duration $+ s }
  }
  return %my_duration
}

; alias safe return $decode( $encode($1-,m),m )

alias on/off {
  if ($nick isop #) && ($2) {
    if ($istok(on,$2,32)) {
      set % $+ $3 $+ .status. $+ $chan on
      if ($5) { msg # $5 is on }
      else { msg # $3 is on }
      return on
    }
    if ($istok(off,$2,32)) {
      set % $+ $3 $+ .status. $+ $chan off
      if ($5) { msg # $5 is off }
      else { msg # $3 is off }
      return off
    }
    if ($istok(mod,$2,32)) {
      set % $+ $3 $+ .status. $+ $chan mod
      if ($5) { msg # $5 is mod only }
      else { msg # $3 is mod only }
      return mod
    }
  }
  if (% [ $+ [ $3 ] ] [ $+ .status. ] [ $+ [ $chan ] ] == off) { return was_off }
  elseif (% [ $+ [ $3 ] ] [ $+ .status. ] [ $+ [ $chan ] ] == mod) && ($nick isop #) {
    msg # $4
    return msg
  }
  elseif (% [ $+ [ $3 ] ] [ $+ .status. ] [ $+ [ $chan ] ] == mod) {
    return was_mod_!msg
  }
  else {
    msg # $4
    return msg
  }
}

alias capital return $upper($left($1,1)) $+ $mid($1,2-)
alias randomviewer return $capital($nick(#,$rand(1,$nick(#,0))))
alias rswiki return runescape.wikia.com/wiki/ $+ $replace($1-,$chr(32),$chr(95))
alias rswiki07 return 2007.runescape.wikia.com/wiki/ $+ $replace($1-,$chr(32),$chr(95))
alias wiki return wikipedia.org/wiki/ $+ $replace($1-,$chr(32),$chr(95))
