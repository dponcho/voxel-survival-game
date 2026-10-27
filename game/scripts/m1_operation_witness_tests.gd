extends Node

func _ready() -> void:
	var output: String = ""
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--operation-witness-output="):
			output = argument.trim_prefix("--operation-witness-output=")
	var probe = ClassDB.instantiate("CairnProbe")
	var native: Dictionary = probe.operation_witness_controls(output + ".events")
	var passed: bool = not output.is_empty() and bool(native.get("passed", false))
	var report: Dictionary = {"schema": "cairn-operation-witness-proof-1", "build": JSON.parse_string(FileAccess.get_file_as_string("res://build_info.json")),
		"native": native, "passed": passed, "qualified": false, "target_performance": "not_run", "route_executed": false,
		"scope": "Perturbing bounded operation controls; injected guards, counter errors and overflow remain failed. No CPU/time conversion or shipping-cost qualification.",
		"trace_sha256": FileAccess.get_sha256(output + ".events")}
	var writer_start: Dictionary = probe.cpu_cycle_observation()
	var writer_begin: int = Time.get_ticks_usec()
	var text: String = JSON.stringify(report, "  ")
	var total: int = text.to_utf8_buffer().size() + int(native.get("witness", {}).get("bytes", 0))
	var saved: bool = total <= 262144 - 8192
	var file: FileAccess = FileAccess.open(output, FileAccess.WRITE) if saved else null
	saved = saved and file != null
	if file != null:
		file.store_string(text)
		file.flush()
		saved = saved and file.get_error() == OK
		file.close()
		file = null
	var writer_end: int = Time.get_ticks_usec()
	var writer_finish: Dictionary = probe.cpu_cycle_observation()
	# This terminal receipt reports the complete proof JSON writer, including
	# serialization/open/write/flush/close/release. Its own write is excluded.
	var receipt: Dictionary = {"schema": "cairn-operation-witness-writer-1", "start": writer_start, "end": writer_finish,
		"begin_usec": str(writer_begin), "end_usec": str(writer_end), "proof_bytes": text.to_utf8_buffer().size(),
		"proof_sha256": FileAccess.get_sha256(output), "trace_and_proof_bytes": total, "passed": saved,
		"terminal_receipt_write_included": false}
	var receipt_text: String = JSON.stringify(receipt, "  ")
	saved = saved and total + receipt_text.to_utf8_buffer().size() <= 262144
	file = FileAccess.open(output + ".writer.json", FileAccess.WRITE) if saved else null
	saved = saved and file != null
	if file != null:
		file.store_string(receipt_text)
		file.flush()
		saved = saved and file.get_error() == OK
		file.close()
	print("CAIRN_OPERATION_WITNESS=" + JSON.stringify({"passed": passed and saved, "output": output}))
	get_tree().quit(0 if passed and saved else 1)
