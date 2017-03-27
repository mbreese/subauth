import os

class Config(object):
	def __init__(self, filename=None, values=None):
		if values:
			self._values = values
		else:
			self._values = {}

		if filename:
			if not os.path.exists(filename):
				raise RuntimeError("Missing config file: %s\n" % filename)
			
			with open(filename) as f:
				for line in f:
					if line.strip() == '' or line[0] == '#':
						continue

					if '=' in line:
						cols = line.strip().split('=')
						self._values[cols[0].strip()] = autotype(cols[1].strip())
					else:
						self._values[line.strip()] = True

	def get_prefix(self, prefix):
		vals = {}
		for k in self._values:
			if k[:len(prefix)] == prefix:
				vals[k[len(prefix):]] = self._values[k]
		return Config(values=vals)

	def dump(self):
		for k in self._values:
			print "%s => %s" % (k, self._values[k])

	def contains(self, key):
		return key in self._values

	def get(self, key, default_val=None):
		if key in self._values:
			return self._values[key]
		return default_val


def autotype(val):
	try:
		f = float(val)
		return f
	except:
		try:
			i = int(val)
			return i
		except:
			if val.upper() in ['T', 'TRUE']:
				return True
			elif val.upper() in ['F', 'FALSE']:
				return False

			return val
