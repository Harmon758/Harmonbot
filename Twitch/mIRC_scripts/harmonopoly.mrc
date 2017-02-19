
; harmonopoly
; add timers notifications?, notification of someone chosen?, +X option?, check if everyone chosen?

on $*:text:/^[!](harmonopoly|hrmp)/Si:#:{
  if (!$2 || $2 == help) {
    msg # Harmonopoly is a game based on The Centipede Game where every player chooses a number. $&
      The player with the lowest number that is not surpassed within +2 of another number that is chosen, wins. The winner gets points equal to the number that they chose. $&
      Examples: {1,2 Winner(W): 2} {1,3 W: 3} {1,4 W: 1} {1,3,5 W: 5} {1,3,5,7,10 W: 7}
    return
  }
  elseif ($2 == credit || $2 == credits) {
    msg # Credit for the name of the game as well as helping to create the game to Australianified. Credit for help debugging to both PMForNudes and Australianified.
    return
  }
  if ($nick isop #) && ($2) {
    if ($2 == start && %harmonopoly.status != off) {
      msg # $capital($nick) $+ , there is already a game of Harmonopoly in progress.
      return
    }
    elseif ($2 == start && $3 isnum && $3 > 0) {
      set %harmonopoly.status on.start
      var %interval = $calc($3 * 60)
      msg # $capital($nick) has started a game of Harmonopoly! Everyone has $3 minute(s) to !harmonopoly enter.
      .timerharmonopoly 1 %interval .harmonopoly $chan %interval
      return
    }
    elseif ($2 == end) {
      set %harmonopoly.status off
      set %harmonopoly.players
      set %harmonopoly.entries
      msg # $capital($nick) has ended the current game of Harmonopoly.
      .timerharmonopoly off
      return
    }
    elseif ($2 != enter && $2 != points && $2 != top) {
      msg # $capital($nick) $+ , please enter !harmonopoly start $chr(35) where $chr(35) is the interval (>0) that you would like or !harmonopoly end.
      return
    }
  }
  if (%harmonopoly.status == on.start && $2 == enter) {
    if ($harmonopoly.isplayer($nick) == true) {
      msg # $capital($nick) $+ , you have already entered the current game of Harmonopoly!
      return
    }
    set %harmonopoly.players %harmonopoly.players $nick
    msg # $capital($nick) $+ , you have entered the current game of Harmonopoly!
    return
  }
  if ($2 == points) {
    if ($nick isop # && $3) {
      if ($findtok(%harmonopoly.names, $3, 0, 32) == 1) {
        var %winner_player_number = $findtok(%harmonopoly.names, $3, 1, 32)
        msg # $capital($3) has $gettok(%harmonopoly.points, %winner_player_number, 32) points.
      }
      else { msg # $capital($3) has not won yet :( }
      return
    }
    if ($findtok(%harmonopoly.names, $nick, 0, 32) == 1) {
      var %winner_player_number = $findtok(%harmonopoly.names, $nick, 1, 32)
      msg # $capital($nick) $+ , you have $gettok(%harmonopoly.points, %winner_player_number, 32) points.
    }
    else { msg # $capital($nick) $+ , you have not won yet :( }
  }
  if ($2 == top) {
    var %top_list = Top: 
    var %points = %harmonopoly.points
    var %names = %harmonopoly.names
    var %sorted_points = $sorttok(%points, 32, nr)
    var %top_sorted_points = $gettok(%sorted_points, 1-10, 32)
    while ($numtok(%top_sorted_points, 32) > 0) {
      var %name_number = $findtok(%points, $gettok(%top_sorted_points, 1, 32), 1, 32)
      var %name = $gettok(%names, %name_number, 32)
      var %top_list = %top_list $capital(%name) $+ : $gettok(%top_sorted_points, 1, 32) 
      %points = $deltok(%points, %name_number, 32)
      %names = $deltok(%names, %name_number, 32)
      %top_sorted_points = $deltok(%top_sorted_points, 1, 32)
    }
    msg # %top_list
  }
}

alias harmonopoly {
  if (%harmonopoly.status == on.start) {
    set %harmonopoly.status on.during
    set %harmonopoly.entries -1
    var %counter = $numtok(%harmonopoly.players, 32)
    if (%counter <= 1) {
      msg $1 The Harmonopoly game has ended because not enough people entered :(
      set %harmonopoly.status off
      set %harmonopoly.players
      set %harmonopoly.entries
      return
    }
    while (%counter > 1) {
      set %harmonopoly.entries %harmonopoly.entries -1
      dec %counter
    }
    msg $1 Harmonopoly has started! Everyone entered has $calc($2 / 60) minute(s) to /w Harmonbot their number.
    .timerharmonopoly 1 $2 .harmonopoly $1
  }
  elseif (%harmonopoly.status == on.during) {
    var %sorted_entries = $sorttok(%harmonopoly.entries, 32, n)
    var %counter = 1
    var %winner_number = -1
    while (%counter < $numtok(%sorted_entries, 32)) {
      if ($gettok(%sorted_entries, %counter, 32) == -1) {
        inc %counter
        continue
      }
      if ($calc($gettok(%sorted_entries, %counter, 32) + 2) < $gettok(%sorted_entries, $calc(%counter + 1), 32)) {
        %winner_number = $gettok(%sorted_entries, %counter, 32)
        break
      }
      inc %counter
    }
    if (%winner_number == -1) { %winner_number = $gettok(%sorted_entries, $numtok(%sorted_entries, 32), 32) }
    if (%winner_number == -1) {
      msg $1 The Harmonopoly game has ended! Nobody won; there weren't any entries :(
      set %harmonopoly.status off
      set %harmonopoly.players
      set %harmonopoly.entries
      return
    }
    var %number_of_winners = $findtok(%harmonopoly.entries, %winner_number, 0, 32)
    var %winner_player_number = $findtok(%harmonopoly.entries, %winner_number, 1, 32)
    var %winner_names = $capital($gettok(%harmonopoly.players, %winner_player_number, 32))
    if (%number_of_winners == 1) { msg $1 The Harmonopoly game has ended! The winner is %winner_names with %winner_number $+ ! }
    else {
      %counter = 2
      while (%counter <= %number_of_winners) {
        %winner_player_number = $findtok(%harmonopoly.entries, %winner_number, %counter, 32)
        %winner_names = %winner_names $+ , $capital($gettok(%harmonopoly.players, %winner_player_number, 32))
        inc %counter
      }
      msg $1 The Harmonopoly game has ended! There was a tie! The winners are %winner_names with %winner_number $+ !
    }
    var %results_list = Results: 
    var %players = %harmonopoly.players
    var %entries = %harmonopoly.entries
    while ($numtok(%players, 32) > 0) {
      if ($gettok(%entries, 1, 32) == -1) { %entries = $puttok(%entries, N/A, 1, 32) }
      var %results_list = %results_list $capital($gettok(%players, 1, 32)) $+ : $gettok(%entries, 1, 32) 
      %players = $deltok(%players, 1, 32)
      %entries = $deltok(%entries, 1, 32)
    }
    msg $1 %results_list
    var %points = %harmonopoly.points
    var %winner_name = -1
    %winner_names = $remove(%winner_names, $chr(44))
    %counter = 1
    while (%counter <= %number_of_winners) {
      %winner_name = $gettok(%winner_names, %counter, 32)
      if ($findtok(%harmonopoly.names, %winner_name, 0, 32) == 1) {
        %winner_player_number = $findtok(%harmonopoly.names, %winner_name, 1, 32)
        %points = $puttok(%points, $calc($gettok(%points, %winner_player_number, 32) + %winner_number), %winner_player_number, 32)
        set %harmonopoly.points %points
      }
      else {
        set %harmonopoly.names %harmonopoly.names %winner_name
        set %harmonopoly.points %harmonopoly.points %winner_number
      }
      inc %counter
    }
    set %harmonopoly.status off
    set %harmonopoly.players
    set %harmonopoly.entries
  }
}

alias harmonopoly.isplayer {
  var %players = %harmonopoly.players
  while ($numtok(%players, 32) > 0) {
    var %player = $gettok(%players, 1 , 32)
    if (%player == $1) { return true }
    %players = $deltok(%players, 1, 32)
  }
  return false
}

raw *:*: {
  if $nick == tmi.twitch.tv {
    if whisper isin $rawmsg {
      tokenize 59 $rawmsg
      var %displayname = $remove($2, display-name=)
      var %message = $gettok($5, 3, 58)
      if (%harmonopoly.status == on.during) {
        if ($harmonopoly.isplayer(%displayname) == true) {
          var %number = $int($gettok(%message, 1, 32))
          if (%number isnum && %number > 0) {
            /msg jtv /w %displayname You have chosen %number $+ .
            var %player_number = $findtok(%harmonopoly.players, $lower(%displayname), 1, 32)
            set %harmonopoly.entries $puttok(%harmonopoly.entries, %number, %player_number, 32)
          }
          else { /msg jtv /w %displayname Please enter a number greater than 0. }
        }
      }
    }
  }
}
