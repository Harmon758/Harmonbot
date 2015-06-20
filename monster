;
; http://services.runescape.com/m=rswiki/en/Bestiary_APIs
;

on *:text:!monster*:#:{
  if (!$2) {
    msg # Please specify a monster.
    return
  }
  var %url = http://services.runescape.com/m=itemdb_rs/bestiary/beastSearch.json?term= $+ $replace($2-,$chr(32),$chr(43))
  var %monster_id = $json(%url,0,value)
  var %url = http://services.runescape.com/m=itemdb_rs/bestiary/beastData.json?beastid= $+ %monster_id
  if ($json(%url,members) == $true) { var %monster_members = Yes }
  else { var %monster_members = No }
  if ($json(%url,aggressive) == $true) { var %monster_aggressive = Yes }
  else { var %monster_aggressive = No }
  if (%monster_id) { msg # $json(%url,name) $+ , $json(%url,description) $+ , Level: $json(%url,level) $+ , Weakness: $json(%url,weakness) $&
    $+ , XP/Kill: $json(%url,xp) $+ , Lifepoints: $json(%url,lifepoints) $+ , Members: %monster_members $+ , Aggressive: %monster_aggressive }
  else { msg # Monster $2- not found. }
}
