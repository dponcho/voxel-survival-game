extends RefCounted

# Small decimal arithmetic for raw uint64 counters and unbounded rational cross
# products. Never parse a cycle string through float or Godot's signed int64.
static func canonical(a: Variant, unsigned: bool = false) -> bool:
	if not a is String or a.is_empty(): return false
	var value: String = a
	if value.begins_with("-"):
		if unsigned: return false
		value = value.substr(1)
		if value == "0": return false
	if value.is_empty() or (value.length() > 1 and value[0] == "0"): return false
	for digit: String in value:
		if digit < "0" or digit > "9": return false
	return true

static func cmp(a: String, b: String) -> int:
	if a == b: return 0
	var an: bool = a.begins_with("-")
	var bn: bool = b.begins_with("-")
	if an != bn: return -1 if an else 1
	if an: return -cmp(a.substr(1), b.substr(1))
	if a.length() != b.length(): return -1 if a.length() < b.length() else 1
	return -1 if a < b else 1

static func neg(a: String) -> String:
	return a.substr(1) if a.begins_with("-") else ("0" if a == "0" else "-" + a)

static func add(a: String, b: String) -> String:
	if a.begins_with("-"): return neg(add(a.substr(1), neg(b)))
	if b.begins_with("-"):
		var v: String = b.substr(1)
		if cmp(a, v) < 0: return neg(sub(v, a))
		var borrow: int = 0
		var output: String = ""
		for i: int in range(a.length()):
			var digit: int = int(a[a.length() - 1 - i]) - borrow - (int(v[v.length() - 1 - i]) if i < v.length() else 0)
			borrow = 1 if digit < 0 else 0
			output = str(digit + borrow * 10) + output
		while output.length() > 1 and output[0] == "0": output = output.substr(1)
		return output
	var carry: int = 0
	var result: String = ""
	for i: int in range(maxi(a.length(), b.length())):
		var digit: int = carry + (int(a[a.length() - 1 - i]) if i < a.length() else 0) + (int(b[b.length() - 1 - i]) if i < b.length() else 0)
		result = str(digit % 10) + result
		carry = digit / 10
	return (str(carry) if carry else "") + result

static func sub(a: String, b: String) -> String: return add(a, neg(b))
static func absolute(a: String) -> String: return a.substr(1) if a.begins_with("-") else a
static func low(a: String, b: String) -> String: return a if cmp(a, b) <= 0 else b
static func high(a: String, b: String) -> String: return a if cmp(a, b) >= 0 else b

static func mul(a: String, b: String) -> String:
	if a.begins_with("-"): return neg(mul(a.substr(1), b))
	if b.begins_with("-"): return neg(mul(a, b.substr(1)))
	var result: String = "0"
	var zeros: String = ""
	for j: int in range(b.length() - 1, -1, -1):
		var row: String = ""
		var carry: int = 0
		for i: int in range(a.length() - 1, -1, -1):
			var value: int = int(a[i]) * int(b[j]) + carry
			row = str(value % 10) + row
			carry = value / 10
		if carry: row = str(carry) + row
		while row.length() > 1 and row[0] == "0": row = row.substr(1)
		result = add(result, row + zeros if row != "0" else "0")
		zeros += "0"
	return result

static func divide_small(a: String, divisor: int, ceiling: bool = false) -> String:
	var result: String = ""
	var remainder: int = 0
	for digit: String in a:
		remainder = remainder * 10 + int(digit)
		result += str(remainder / divisor)
		remainder %= divisor
	while result.length() > 1 and result[0] == "0": result = result.substr(1)
	return add(result, "1") if ceiling and remainder else result

static func ratio(n: String, d: String = "1") -> Dictionary: return {"n": n, "d": d}
static func radd(a: Dictionary, b: Dictionary) -> Dictionary:
	return ratio(add(mul(a.n, b.d), mul(b.n, a.d)), mul(a.d, b.d))
static func rsub(a: Dictionary, b: Dictionary) -> Dictionary: return radd(a, ratio(neg(b.n), b.d))
static func rcmp(a: Dictionary, b: Dictionary) -> int: return cmp(mul(a.n, b.d), mul(b.n, a.d))
static func rmax(a: Dictionary, b: Dictionary) -> Dictionary: return a if rcmp(a, b) >= 0 else b
static func midpoint(bounds: Array) -> String: return add(bounds[0], divide_small(sub(bounds[1], bounds[0]), 2))
