; ***REMOVED***
;
on *:text:!ehp*:#:{
  if (!$2) { msg # Please specify a skill and amount of xp. }
  elseif ($2 isnum) { msg # Please specify a skill. }
  elseif (!$3) { msg # Please specify amount of xp. }
  elseif ($3 !isnum) { msg # Sytax error. }
  elseif ($3 isnum && $3 > 200000000) { msg # You can't have that much xp, $capital($nick) ! Reported. }
  elseif ($2 == attack || $2 == att) {
    if ($3 >= 0 && $3 < 37224) { msg # At $3 Attack xp: 1 ehp = 15,000 xp/h }
    elseif ($3 >= 37224 && $3 < 100000) { msg # At $3 Attack xp: 1 ehp = 38,000 xp/h }
    elseif ($3 >= 100000 && $3 < 1000000) { msg # At $3 Attack xp: 1 ehp = 55,000 xp/h }
    elseif ($3 >= 1000000 && $3 < 1986068) { msg # At $3 Attack xp: 1 ehp = 65,000 xp/h }
    elseif ($3 >= 1986068 && $3 < 3000000) { msg # At $3 Attack xp: 1 ehp = 80,000 xp/h }
    elseif ($3 >= 3000000 && $3 < 5346332) { msg # At $3 Attack xp: 1 ehp = 90,000 xp/h }
    elseif ($3 >= 5346332 && $3 < 13034431) { msg # At $3 Attack xp: 1 ehp = 105,000 xp/h }
    elseif ($3 >= 13034431) { msg # At $3 Attack xp: 1 ehp = 120,000 xp/h }
  }
  elseif ($2 == defence || $2 == def) {
    if ($3 >= 0 && $3 < 37224) { msg # At $3 Defence xp: 1 ehp = 15,000 xp/h }
    elseif ($3 >= 37224 && $3 < 100000) { msg # At $3 Defence xp: 1 ehp = 38,000 xp/h }
    elseif ($3 >= 100000 && $3 < 1000000) { msg # At $3 Defence xp: 1 ehp = 55,000 xp/h }
    elseif ($3 >= 1000000 && $3 < 1986068) { msg # At $3 Defence xp: 1 ehp = 65,000 xp/h }
    elseif ($3 >= 1986068 && $3 < 3000000) { msg # At $3 Defence xp: 1 ehp = 80,000 xp/h }
    elseif ($3 >= 3000000 && $3 < 5346332) { msg # At $3 Defence xp: 1 ehp = 90,000 xp/h }
    elseif ($3 >= 5346332 && $3 < 13034431) { msg # At $3 Defence xp: 1 ehp = 105,000 xp/h }
    elseif ($3 >= 13034431) { msg # At $3 Defence xp: 1 ehp = 120,000 xp/h }
  }
  elseif ($2 == strength || $2 == str) {
    if ($3 >= 0 && $3 < 37224) { msg # At $3 Strength xp: 1 ehp = 15,000 xp/h }
    elseif ($3 >= 37224 && $3 < 100000) { msg # At $3 Strength xp: 1 ehp = 38,000 xp/h }
    elseif ($3 >= 100000 && $3 < 1000000) { msg # At $3 Strength xp: 1 ehp = 55,000 xp/h }
    elseif ($3 >= 1000000 && $3 < 1986068) { msg # At $3 Strength xp: 1 ehp = 65,000 xp/h }
    elseif ($3 >= 1986068 && $3 < 3000000) { msg # At $3 Strength xp: 1 ehp = 80,000 xp/h }
    elseif ($3 >= 3000000 && $3 < 5346332) { msg # At $3 Strength xp: 1 ehp = 90,000 xp/h }
    elseif ($3 >= 5346332 && $3 < 13034431) { msg # At $3 Strength xp: 1 ehp = 105,000 xp/h }
    elseif ($3 >= 13034431) { msg # At $3 Strength xp: 1 ehp = 120,000 xp/h }
  }
  elseif ($2 == hitpoints || $2 == hp) { msg # None. }
  elseif ($2 == ranged || $2 == range) {
    if ($3 >= 0 && $3 < 6517253) { msg # At $3 Ranged xp: 1 ehp = 250,000 xp/h }
    elseif ($3 >= 6517253 && $3 < 13034431) { msg # At $3 Ranged xp: 1 ehp = 330,000 xp/h }
    elseif ($3 >= 13034431) { msg # At $3 Ranged xp: 1 ehp = 350,000 xp/h }
  }
  elseif ($2 == prayer || $2 == pray) { msg # For Prayer: 1 ehp = 500,000 xp/h }
  elseif ($2 == magic || $2 == mage) { msg # For Magic: 1 ehp = 250,000 xp/h }
  elseif ($2 == cooking || $2 == cook) {
    if ($3 >= 0 && $3 < 7842) { msg # At $3 Cooking xp: 1 ehp = 40,000 xp/h }
    elseif ($3 >= 7842 && $3 < 37224) { msg # At $3 Cooking xp: 1 ehp = 130,000 xp/h }
    elseif ($3 >= 37224 && $3 < 1986068) { msg # At $3 Cooking xp: 1 ehp = 175,000 xp/h }
    elseif ($3 >= 1986068 && $3 < 5346332) { msg # At $3 Cooking xp: 1 ehp = 275,000 xp/h }
    elseif ($3 >= 5346332 && $3 < 7944614) { msg # At $3 Cooking xp: 1 ehp = 340,000 xp/h }
    elseif ($3 >= 7944614) { msg # At $3 Cooking xp: 1 ehp = 360,000 xp/h }
  }
  elseif ($2 == woodcutting || $2 == wc) {
    if ($3 >= 0 && $3 < 2411) { msg # At $3 Woodcutting xp: 1 ehp = 7,000 xp/h }
    elseif ($3 >= 2411 && $3 < 13363) { msg # At $3 Woodcutting xp: 1 ehp = 16,000 xp/h }
    elseif ($3 >= 13363 && $3 < 41171) { msg # At $3 Woodcutting xp: 1 ehp = 35,000 xp/h }
    elseif ($3 >= 41171 && $3 < 302288) { msg # At $3 Woodcutting xp: 1 ehp = 49,000 xp/h }
    elseif ($3 >= 302288 && $3 < 500000) { msg # At $3 Woodcutting xp: 1 ehp = 58,000 xp/h }
    elseif ($3 >= 500000 && $3 < 1000000) { msg # At $3 Woodcutting xp: 1 ehp = 68,000 xp/h }
    elseif ($3 >= 1000000 && $3 < 2000000) { msg # At $3 Woodcutting xp: 1 ehp = 73,000 xp/h }
    elseif ($3 >= 2000000 && $3 < 4000000) { msg # At $3 Woodcutting xp: 1 ehp = 80,000 xp/h }
    elseif ($3 >= 4000000 && $3 < 8000000) { msg # At $3 Woodcutting xp: 1 ehp = 86,000 xp/h }
    elseif ($3 >= 8000000) { msg # At $3 Woodcutting xp: 1 ehp = 92,000 xp/h }
  }
  elseif ($2 == fletching || $2 == fletch) {
    if ($3 >= 0 && $3 < 7842) { msg # At $3 Fletching xp: 1 ehp = 30,000 xp/h }
    elseif ($3 >= 7842 && $3 < 22406) { msg # At $3 Fletching xp: 1 ehp = 45,000 xp/h }
    elseif ($3 >= 22406 && $3 < 166636) { msg # At $3 Fletching xp: 1 ehp = 72,000 xp/h }
    elseif ($3 >= 166636 && $3 < 737627) { msg # At $3 Fletching xp: 1 ehp = 135,000 xp/h }
    elseif ($3 >= 737627 && $3 < 3258594) { msg # At $3 Fletching xp: 1 ehp = 184,000 xp/h }
    elseif ($3 >= 3258594) { msg # At $3 Fletching xp: 1 ehp = 225,000 xp/h }
  }
  elseif ($2 == fishing || $2 == fish) {
    if ($3 >= 0 && $3 < 4470) { msg # At $3 Fishing xp: 1 ehp = 14,000 xp/h }
    elseif ($3 >= 4470 && $3 < 13363) { msg # At $3 Fishing xp: 1 ehp = 30,000 xp/h }
    elseif ($3 >= 13363 && $3 < 273742) { msg # At $3 Fishing xp: 1 ehp = 40,000 xp/h }
    elseif ($3 >= 273742 && $3 < 737627) { msg # At $3 Fishing xp: 1 ehp = 44,000 xp/h }
    elseif ($3 >= 737627 && $3 < 2500000) { msg # At $3 Fishing xp: 1 ehp = 52,000 xp/h }
    elseif ($3 >= 2500000 && $3 < 6000000) { msg # At $3 Fishing xp: 1 ehp = 56,500 xp/h }
    elseif ($3 >= 6000000 && $3 < 11000000) { msg # At $3 Fishing xp: 1 ehp = 59,000 xp/h }
    elseif ($3 >= 11000000 && $3 < 13034431) { msg # At $3 Fishing xp: 1 ehp = 61,000 xp/h }
    elseif ($3 >= 13034431) { msg # At $3 Fishing xp: 1 ehp = 63,000 xp/h }
  }
  elseif ($2 == firemaking || $2 == fm) {
    if ($3 >= 0 && $3 < 13363) { msg # At $3 Firemaking xp: 1 ehp = 45,000 xp/h }
    elseif ($3 >= 13363 && $3 < 61512) { msg # At $3 Firemaking xp: 1 ehp = 130,500 xp/h }
    elseif ($3 >= 61512 && $3 < 273742) { msg # At $3 Firemaking xp: 1 ehp = 195,750 xp/h }
    elseif ($3 >= 273742 && $3 < 1210421) { msg # At $3 Firemaking xp: 1 ehp = 293,625 xp/h }
    elseif ($3 >= 1210421) { msg # At $3 Firemaking xp: 1 ehp = 445,000 xp/h }
  }
  elseif ($2 == crafting || $2 == craft) {
    if ($3 >= 0 && $3 < 300000) { msg # At $3 Crafting xp: 1 ehp = 57,000 xp/h }
    elseif ($3 >= 300000 && $3 < 362000) { msg # At $3 Crafting xp: 1 ehp = 170,000 xp/h }
    elseif ($3 >= 362000) { msg # At $3 Crafting xp: 1 ehp = 285,000 xp/h }
  }
  elseif ($2 == smithing || $2 == smith) {
    if ($3 >= 0 && $3 < 37224) { msg # At $3 Smithing xp: 1 ehp = 40,000 xp/h }
    elseif ($3 >= 37224) { msg # At $3 Smithing xp: 1 ehp = 103,000 xp/h }
  }
  elseif ($2 == mining || $2 == mine) {
    if ($3 >= 0 && $3 < 14883) { msg # At $3 Mining xp: 1 ehp = 8,000 xp/h }
    elseif ($3 >= 14833 && $3 < 41171) { msg # At $3 Mining xp: 1 ehp = 20,000 xp/h }
    elseif ($3 >= 41171 && $3 < 302288) { msg # At $3 Mining xp: 1 ehp = 44,000 xp/h }
    elseif ($3 >= 302288 && $3 < 547953) { msg # At $3 Mining xp: 1 ehp = 47,000 xp/h }
    elseif ($3 >= 547953 && $3 < 1986068) { msg # At $3 Mining xp: 1 ehp = 54,000 xp/h }
    elseif ($3 >= 1986068 && $3 < 6000000) { msg # At $3 Mining xp: 1 ehp = 58,000 xp/h }
    elseif ($3 >= 6000000) { msg # At $3 Mining xp: 1 ehp = 63,000 xp/h }
  }
  elseif ($2 == herblore || $2 == herb) {
    if ($3 >= 0 && $3 < 27473) { msg # At $3 Herblore xp: 1 ehp = 60,000 xp/h }
    elseif ($3 >= 27473 && $3 < 2192818) { msg # At $3 Herblore xp: 1 ehp = 200,000 xp/h }
    elseif ($3 >= 2192818) { msg # At $3 Herblore xp: 1 ehp = 310,000 xp/h }
  }
  elseif ($2 == agility) {
    if ($3 >= 0 && $3 < 13363) { msg # At $3 Agility xp: 1 ehp = 6,000 xp/h }
    elseif ($3 >= 13363 && $3 < 41171) { msg # At $3 Agility xp: 1 ehp = 15,000 xp/h }
    elseif ($3 >= 41171 && $3 < 449428) { msg # At $3 Agility xp: 1 ehp = 44,000 xp/h }
    elseif ($3 >= 449428 && $3 < 2192818) { msg # At $3 Agility xp: 1 ehp = 50,000 xp/h }
    elseif ($3 >= 2192818 && $3 < 6000000) { msg # At $3 Agility xp: 1 ehp = 55,000 xp/h }
    elseif ($3 >= 6000000 && $3 < 11000000) { msg # At $3 Agility xp: 1 ehp = 59,000 xp/h }
    elseif ($3 >= 11000000) { msg # At $3 Agility xp: 1 ehp = 62,000 xp/h }
  }
  elseif ($2 == thieving || $2 == thief || $2 == thieve) {
    if ($3 >= 0 && $3 < 61512) { msg # At $3 Thieving xp: 1 ehp = 15,000 xp/h }
    elseif ($3 >= 61512 && $3 < 166636) { msg # At $3 Thieving xp: 1 ehp = 60,000 xp/h }
    elseif ($3 >= 166636 && $3 < 449428) { msg # At $3 Thieving xp: 1 ehp = 100,000 xp/h }
    elseif ($3 >= 449428 && $3 < 5902831) { msg # At $3 Thieving xp: 1 ehp = 220,000 xp/h }
    elseif ($3 >= 5902831 && $3 < 13034431) { msg # At $3 Thieving xp: 1 ehp = 255,000 xp/h }
    elseif ($3 >= 13034431) { msg # At $3 Thieving xp: 1 ehp = 265,000 xp/h }
  }
  elseif ($2 == slayer || $2 == slay) {
    if ($3 >= 0 && $3 < 37224) { msg # At $3 Slayer xp: 1 ehp = 5,000 xp/h }
    elseif ($3 >= 37224 && $3 < 100000) { msg # At $3 Slayer xp: 1 ehp = 12,000 xp/h }
    elseif ($3 >= 100000 && $3 < 1000000) { msg # At $3 Slayer xp: 1 ehp = 17,000 xp/h }
    elseif ($3 >= 1000000 && $3 < 1986068) { msg # At $3 Slayer xp: 1 ehp = 25,000 xp/h }
    elseif ($3 >= 1986068 && $3 < 3000000) { msg # At $3 Slayer xp: 1 ehp = 30,000 xp/h }
    elseif ($3 >= 3000000 && $3 < 7195629) { msg # At $3 Slayer xp: 1 ehp = 32,500 xp/h }
    elseif ($3 >= 7195629 && $3 < 13034431) { msg # At $3 Slayer xp: 1 ehp = 35,000 xp/h }
    elseif ($3 >= 13034431) { msg # At $3 Slayer xp: 1 ehp = 37,000 xp/h }
  }
  elseif ($2 == farming || $2 == farm) {
    if ($3 >= 0 && $3 < 2411) { msg # At $3 Farming xp: 1 ehp = 10,000 xp/h }
    elseif ($3 >= 2411 && $3 < 13363) { msg # At $3 Farming xp: 1 ehp = 50,000 xp/h }
    elseif ($3 >= 13363 && $3 < 61512) { msg # At $3 Farming xp: 1 ehp = 80,000 xp/h }
    elseif ($3 >= 61512 && $3 < 273742) { msg # At $3 Farming xp: 1 ehp = 150,000 xp/h }
    elseif ($3 >= 273742 && $3 < 1210421) { msg # At $3 Farming xp: 1 ehp = 350,000 xp/h }
    elseif ($3 >= 1210421) { msg # At $3 Farming xp: 1 ehp = 700,000 xp/h }
  }
  elseif ($2 == runecrafting || $2 == rc) {
    if ($3 >= 0 && $3 < 2107) { msg # At $3 Runecrafting xp: 1 ehp = 8,000 xp/h }
    elseif ($3 >= 2107 && $3 < 1210421) { msg # At $3 Runecrafting xp: 1 ehp = 20,000 xp/h }
    elseif ($3 >= 1210421 && $3 < 2421087) { msg # At $3 Runecrafting xp: 1 ehp = 24,500 xp/h }
    elseif ($3 >= 2421087 && $3 < 5902831) { msg # At $3 Runecrafting xp: 1 ehp = 30,000 xp/h }
    elseif ($3 >= 5902831) { msg # At $3 Runecrafting xp: 1 ehp = 26,250 xp/h }
  }
  elseif ($2 == hunter || $2 == hunt) {
    if ($3 >= 0 && $3 < 12031) { msg # At $3 Hunter xp: 1 ehp = 5,000 xp/h }
    elseif ($3 >= 12031 && $3 < 247886) { msg # At $3 Hunter xp: 1 ehp = 40,000 xp/h }
    elseif ($3 >= 247886 && $3 < 1986068) { msg # At $3 Hunter xp: 1 ehp = 80,000 xp/h }
    elseif ($3 >= 1986068 && $3 < 3972294) { msg # At $3 Hunter xp: 1 ehp = 110,000 xp/h }
    elseif ($3 >= 3972294 && $3 < 13034431) { msg # At $3 Hunter xp: 1 ehp = 135,000 xp/h }
    elseif ($3 >= 13034431) { msg # At $3 Hunter xp: 1 ehp = 155,000 xp/h }
  }
  elseif ($2 == construction || $2 == con) {
    if ($3 >= 0 && $3 < 18247) { msg # At $3 Construction xp: 1 ehp = 20,000 xp/h }
    elseif ($3 >= 18247 && $3 < 101333) { msg # At $3 Construction xp: 1 ehp = 100,000 xp/h }
    elseif ($3 >= 101333 && $3 < 1096278) { msg # At $3 Construction xp: 1 ehp = 230,000 xp/h }
    elseif ($3 >= 1096278) { msg # At $3 Construction xp: 1 ehp = 410,000 xp/h }
  }
}
