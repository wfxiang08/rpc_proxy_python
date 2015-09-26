struct Location {
	1:string city,
	2:string province,
	3:list<string> names
}

struct Locations {
	1:required list<Location> locations,
	2:optional list<string> strs,
	3:optional list<i32> ints,
}


