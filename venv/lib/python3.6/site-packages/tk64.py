

class TokenError(Exception):
	
	def __init__(self, msg):

		self.message = msg

	def __str__(self):
		return repr(self.message)

class Token(object):

	INT64 = 9223372036854775807

	def __init__(self, alphabet):

		self.alphabet = alphabet
		self.len = len(alphabet)

	def encode(self, n):

		if n > self.INT64 or (-self.INT64 - 1) > n:
			raise TokenError('Number must fit in 64 bit range.')

		NEG = True if n < 0 else False

		if NEG:
			n = (self.INT64 * 2) + n + 2

		d = []

		while n >= self.len:

			n, r = divmod(n, self.len)
			symbol = self.alphabet[r]
			d.append(symbol)

		d.append(self.alphabet[n])

		return ''.join(str(x) for x in list(reversed(d)))
		
	def decode(self, n):

		NLEN = len(n) - 1
		d = 0

		if n == '':
			raise TokenError('Empty strings are forbidden')

		for i, x in enumerate(n):

			try:
				pos = self.alphabet.index(x)
			except ValueError:
				raise TokenError('Token contains invalid char for this alphabet')
			num = pos * pow(self.len, NLEN - i)
			d += num

		NEG = True if d > self.INT64 else False

		if NEG:
			d = d - (2 * self.INT64) - 2

		if d > self.INT64 or (-self.INT64 - 1) > d:
			raise TokenError('Number must fit in 64 bit range.')

		return d
