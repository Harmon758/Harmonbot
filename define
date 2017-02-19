; ***REMOVED***
; 
; http://developer.wordnik.com/docs.html

on *:text:!define*:#:{
  if ($define($2)) { msg # $capital(%define_word) $+ : $define($2) }
  else { msg # Definition not found. }
}

on *:text:!audiodefine*:#:{
  if ($audiodefine($2)) { msg # $capital(%define_word) $+ : $audiodefine($2) }
  else { msg # Word or audio not found. }
}

on *:text:!randomword*:#:{
  var %url = http://api.wordnik.com:80/v4/words.json/randomWord?hasDictionaryDef=false&minCorpusCount=0&maxCorpusCount=-1&minDictionaryCount=1&maxDictionaryCount=-1&minLength=5&maxLength=-1&api_key=***REMOVED***
  msg # $json(%url,word)
}

alias define {
  var %url = http://api.wordnik.com:80/v4/word.json/ $+ $1 $+ /definitions?limit=1&includeRelated=false&useCanonical=false&includeTags=false&api_key=***REMOVED***
  var %definition = $json(%url,0,text)
  set %define_word $json(%url,0,word)
  return %definition
}

alias audiodefine {
  var %url = http://api.wordnik.com:80/v4/word.json/ $+ $1 $+ /audio?useCanonical=false&limit=1&api_key=***REMOVED***
  var %audio = $json(%url,0,fileUrl)
  set %define_word $json(%url,0,word)
  return %audio
}
