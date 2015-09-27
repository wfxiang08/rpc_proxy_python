struct Location {
	1:string city,
	2:string province,
	3:list<string> names
}

struct Locations {
	1:required list<Location> locations,
	2:optional list<string> strs,
	3:optional list<i32> ints,
	4:optional map<i32, string> id2name,
	5:optional map<i32, Location> id2loc,
	6:optional Location loc,
	7:optional list<Location> loc_list,
	8:optional list<map<i32, Location>> list_map,
}


