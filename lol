
; API Key: ***REMOVED***

on *:text:!lollvl*:#:{
  var %url = https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/ $+ $2 $+ ?api_key=***REMOVED***
  if ($json(%url,$2)) {
    msg # $capital($2) is level $json(%url,$2,summonerLevel)
  }
  else {

  }
}

on *:text:!loltotalgames*:#:{
  var %url = https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/ $+ $2 $+ ?api_key=***REMOVED***
  if ($json(%url,$2)) { var %id = $json(%url,$2,id) }
  else {

  }
  %url = https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/ $+ %id $+ ?api_key=***REMOVED***
  msg # $capital($2) has played $json(%url,totalGames) total games.
}

on *:text:!currentgame*:#:{
  var %url = https://na.api.pvp.net/observer-mode/rest/consumer/getSpectatorGameInfo/NA1/41936598?api_key=***REMOVED***
  if ($2 == time && $json(%url,gameLength)) {
    msg # $my_duration($json(%url,gameLength))
  }
  elseif (%2 == participants) {
    var %counter = 0
    var %participants = P:
    msg # test
    while (%counter <= 9) {
      %participants = %participants $+ $json(%url,participants,%counter,summonerName)
      inc %counter
    }
    msg # %participants
  }
}
