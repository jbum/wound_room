# yarrow.py

# returns random integer from 1-64 using a simulation of the yarrow-stalk oracle, 
# as described on pages 721-723 of The I-Ching, Wilhelm/Baynes, Third Edition, Bollinbger Foundation, Princeton University Press 1980 printing.

import random

# this is intended to produce a gaussian distribution that weights towards the center, since people will typically produce more even splits
def split_pile(v):
	a1 = random.randint(1,v-1)
	a2 = random.randint(1,v-1)
	heap_left = int((a1 + a2)/2.0+0.5) # rounded average
	heap_right = v - heap_left
	return (heap_left, heap_right)


def get_trigram_line():
	nbr_stalks = 50-1


	# first sum
	pile_left,pile_right = split_pile(nbr_stalks)
	p1 = 1
	pile_right -= p1
	p2 = (pile_left % 4)
	p2 = 4 if p2 == 0 else p2
	p3 = (pile_right % 4)
	p3 = 4 if p3 == 0 else p3
	sum_a = (p1+p2+p3)

	nbr_stalks -= sum_a

	# second sum
	pile_left,pile_right = split_pile(nbr_stalks)
	p1 = 1
	pile_right -= p1
	p2 = (pile_left % 4)
	p2 = 4 if p2 == 0 else p2
	p3 = (pile_right % 4)
	p3 = 4 if p3 == 0 else p3
	sum_b = (p1+p2+p3)

	nbr_stalks -= sum_b


	# third sum
	pile_left,pile_right = split_pile(nbr_stalks)
	p1 = 1
	pile_right -= p1
	p2 = (pile_left % 4)
	p2 = 4 if p2 == 0 else p2
	p3 = (pile_right % 4)
	p3 = 4 if p3 == 0 else p3
	sum_c = (p1+p2+p3)
	v = (2 if sum_a == 9 else 3) + (2 if sum_b == 8 else 3) + (2 if sum_c == 8 else 3)
	return (v, sum_a, sum_b, sum_c)


# return number from 1-64
# convert trigram patterns to hexagram numbers
tri_table = [ 1, 43, 14, 34,  9,  5, 26, 11,
             10, 58, 38, 54, 61, 60, 41, 19,
             13, 49, 30, 55, 37, 63, 22, 36,
             25, 17, 21, 51, 42,  3, 27, 24,
             44, 28, 50, 32, 57, 48, 18, 46,
              6, 47, 64, 40, 59, 29,  4,  7,
             33, 31, 56, 62, 53, 39, 52, 15,
             12, 45, 35, 16, 20,  8, 23,  2,
]

def get_hexagram():
	bits = 0
	for b in range(6):
		(v,sa,sb,sc) = get_trigram_line()
		if (v == 7 or v == 9): # yang
			bits |= (1 << b)
	return tri_table[bits]

def get_hexagram_frange(min_v, max_v):
	return min_v + (max_v - min_v)*(get_hexagram()/64.0)

def get_hexagram_irange(min_v, max_v):
	return int(min_v + (max_v - min_v)*(get_hexagram()/64.0) + 0.5)

# buckets = [0] * 64
# nbr_tests = 50

# for i in range(nbr_tests):
# 	t = get_hexagram()
# 	buckets[t-1] += 1
# 	print(t)

# max_bucket = max(buckets)
# for i in range(64):
# 	v = int(buckets[i]/float(max_bucket)*64 + 0.5)
# 	print("%02d %s" % (i+1,"*" * v))


# buckets = [0] * 64
# for i in range(nbr_tests):
# 	t = random.randint(1,64)
# 	buckets[t-1] += 1

# max_bucket = max(buckets)
# for i in range(64):
# 	v = int(buckets[i]/float(max_bucket)*64 + 0.5)
# 	print("%02d %s" % (i+1,"*" * v))
