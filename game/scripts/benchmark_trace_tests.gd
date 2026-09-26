extends RefCounted

# Runs only in the existing cloud smoke route, after the shared writer drains.
static func verify(directory: String, phases: Array[Dictionary], reports: Array[Dictionary]) -> Array[String]:
	var failures: Array[String] = []
	var expected: Dictionary = {}
	var files: Dictionary = {}
	for phase: Dictionary in phases:
		var id: int = int(phase["id"])
		expected[id] = {"frames": 0, "upload_count": 0, "upload_bytes": 0, "upload_usec": 0, "upload_max_usec": 0,
			"deletion_count": 0, "deletion_bytes": 0, "deletion_usec": 0, "deletion_max_usec": 0}
		if phase["tracing"]: files[str(phase["raw_operations"])] = true
		for kind: String in ["upload", "deletion"]:
			if int(phase[kind]["usec"]) != int(phase["native_end"][kind + "_usec"]) - int(phase["native_start"][kind + "_usec"]):
				failures.append("Phase totals disagree with additive lifetime counters")
			if int(phase[kind]["max_usec"]) > int(phase["native_end"][kind + "_max_usec"]):
				failures.append("Phase maximum exceeds lifetime maximum")
	for name: String in files:
		var file := FileAccess.open(directory.path_join(name), FileAccess.READ)
		if file == null:
			failures.append("Missing operation CSV: " + name)
			continue
		var header: PackedStringArray = file.get_csv_line()
		var previous_frame: int = -1
		var previous_end: int = -1
		while not file.eof_reached():
			var fields: PackedStringArray = file.get_csv_line()
			if fields.size() == 1 and fields[0].is_empty(): continue
			if fields.size() != 18 or header.size() != 18:
				failures.append("Malformed operation CSV row")
				break
			var row: Dictionary = {}
			for i: int in range(header.size()): row[header[i]] = int(fields[i])
			if not expected.has(row["phase"]):
				failures.append("Unknown operation phase")
				break
			if int(row["native_frame"]) < previous_frame or int(row["start_usec"]) < previous_end or int(row["end_usec"]) < int(row["start_usec"]):
				failures.append("Operation intervals reordered or overlapping")
			previous_frame = int(row["native_frame"])
			previous_end = int(row["end_usec"])
			var total: Dictionary = expected[row["phase"]]
			total["frames"] += 1
			for kind: String in ["upload", "deletion"]:
				for field: String in ["count", "bytes", "usec"]: total[kind + "_" + field] += row[kind + "_" + field]
				total[kind + "_max_usec"] = maxi(int(total[kind + "_max_usec"]), int(row[kind + "_max_usec"]))
				if int(row[kind + "_count"]) > 0:
					var start: int = int(row[kind + "_max_start_usec"])
					if start < int(row["start_usec"]) or start + int(row[kind + "_max_usec"]) > int(row["end_usec"]):
						failures.append("Slowest operation lies outside its frame segment")
		file.close()
	for phase: Dictionary in phases:
		var total: Dictionary = expected[int(phase["id"])]
		if not phase["tracing"]:
			if int(total["frames"]) != 0: failures.append("A/B baseline unexpectedly emitted operation frames")
			continue
		if int(phase["dropped_frames"]) != 0 or int(total["frames"]) != int(phase["frames"]): failures.append("Operation frame evidence is incomplete")
		for kind: String in ["upload", "deletion"]:
			for field: String in ["count", "bytes", "usec", "max_usec"]:
				if int(total[kind + "_" + field]) != int(phase[kind][field]): failures.append("CSV and phase " + kind + " " + field + " disagree")
	for report: Dictionary in reports:
		if not report["completed"] or report["qualified"]: failures.append("Scenario completion and qualification were conflated")
		var phase: Dictionary = report["operation_phase"]
		for kind: String in ["upload", "deletion"]:
			var reason: String = "Individual " + kind + " exceeded 0.75 ms"
			if (int(phase[kind]["max_usec"]) > 750) != (reason in report["reasons"]): failures.append("Scenario used an incorrect operation maximum")
	return failures
