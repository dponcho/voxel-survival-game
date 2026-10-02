extends RefCounted

# Injected monotonic timestamps make the accounting boundaries testable without sleeps.
# All durations are elapsed wall time, not CPU service time. Nested costs are not added.
var started_usec: int = 0
var callbacks: int = 0
var callback_usec: int = 0
var last_callback_usec: int = 0
var last_callback_end_usec: int = 0
var maximum_callback_usec: int = 0
var block_samples: int = 0
var block_usec: int = 0
var blocks: Array[Dictionary] = []
var overflow: bool = false

# A rejected try-lock/queue submission is retried only between scenarios.
# Yield to the existing worker; never spin or drop a final partial batch.
static func drain_pending(flush: Callable, pending: Callable, failed: Callable, next_frame: Signal, max_attempts: int = 120) -> bool:
	var deadline: int = Time.get_ticks_usec() + 1000000
	for attempt: int in range(max_attempts):
		if failed.call(): return false
		flush.call()
		if not pending.call(): return true
		if Time.get_ticks_usec() >= deadline: return false
		await next_frame
	return false

func start(now: int) -> void:
	started_usec = now

func record_callback(begin: int, end: int) -> void:
	last_callback_usec = end - begin
	last_callback_end_usec = end
	callback_usec += last_callback_usec
	maximum_callback_usec = maxi(maximum_callback_usec, last_callback_usec)
	callbacks += 1

func record_interval(usec: int) -> void:
	block_usec += usec
	block_samples += 1
	if block_usec >= 5000000:
		if blocks.size() < 64:
			blocks.append({"samples": block_samples, "usec": block_usec})
		else: overflow = true
		block_samples = 0
		block_usec = 0

func snapshot(end: int, drain_usec: int) -> Dictionary:
	return {"start_usec": started_usec, "end_usec": end, "elapsed_usec": end - started_usec,
		"callbacks": callbacks, "callback_usec": callback_usec, "last_callback_usec": last_callback_usec,
		"last_callback_end_usec": last_callback_end_usec, "maximum_callback_usec": maximum_callback_usec,
		"finalization_usec": end - last_callback_end_usec, "writer_drain_usec": drain_usec,
		"blocks": blocks.duplicate(true), "partial_block": {"samples": block_samples, "usec": block_usec},
		"overflow": overflow}
