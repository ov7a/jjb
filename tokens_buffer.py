class TokensBuffer:
	def __init__(self, max_memory=None):
		self.last_id = 0
		self.ids = dict()
		self.counter = 0
		self.max_memory = max_memory
	
	def get_id(self, token):
		id = self.ids.get(token)
		if id is None:
			id = self.last_id
			self.ids[token] = id
			self.last_id += 1	
			self.counter += 1
			if self.max_memory is not None and self.counter > self.max_memory:
				self.__init__(self.max_memory)
				return self.get_id(token)
		return id
		
