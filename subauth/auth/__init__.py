class Auth(object):
	def __init__(self, config):
		self.config = config

	def auth(self, username, password):
		raise NotImplementedError