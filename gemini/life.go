package main

import (
	"fmt"
	"math"
	"math/bits"
	"os"
	"strconv"
	"time"
)

func main() {
	if len(os.Args) < 4 {
		fmt.Fprintf(os.Stderr, "Usage: %s N GENS SEED_FILE\n", os.Args[0])
		return
	}

	n, err := strconv.Atoi(os.Args[1])
	if err != nil {
		return
	}
	gens, err := strconv.Atoi(os.Args[2])
	if err != nil {
		return
	}
	filename := os.Args[3]

	fileBytes, err := os.ReadFile(filename)
	if err != nil {
		return
	}

	w := (n + 63) / 64
	rem := n % 64
	var lastMask uint64
	if rem == 0 {
		lastMask = ^uint64(0)
	} else {
		lastMask = (uint64(1) << rem) - 1
	}
	var lastBitIdx uint
	if rem == 0 {
		lastBitIdx = 63
	} else {
		lastBitIdx = uint(rem - 1)
	}

	cur := make([]uint64, n*w)
	nxt := make([]uint64, n*w)

	filePos := 0
	fileLen := len(fileBytes)
	for r := 0; r < n && filePos < fileLen; r++ {
		c := 0
		for c < n && filePos < fileLen {
			b := fileBytes[filePos]
			filePos++
			if b == '1' {
				cur[r*w+(c/64)] |= uint64(1) << (c % 64)
				c++
			} else if b == '0' {
				c++
			}
		}
		for filePos < fileLen && (fileBytes[filePos] == '\r' || fileBytes[filePos] == '\n') {
			filePos++
		}
	}

	s1 := make([]uint64, w)
	c1 := make([]uint64, w)
	s1L := make([]uint64, w)
	s1R := make([]uint64, w)
	c1L := make([]uint64, w)
	c1R := make([]uint64, w)

	t0 := time.Now()

	for g := 0; g < gens; g++ {
		for r := 0; r < n; r++ {
			rUp := r - 1
			if r == 0 {
				rUp = n - 1
			}
			rDn := r + 1
			if r == n-1 {
				rDn = 0
			}

			uOff := rUp * w
			mOff := r * w
			dOff := rDn * w

			for k := 0; k < w; k++ {
				u := cur[uOff+k]
				m := cur[mOff+k]
				d := cur[dOff+k]
				uXorM := u ^ m
				s1[k] = uXorM ^ d
				c1[k] = (u & m) | (d & uXorM)
			}

			for k := 0; k < w; k++ {
				l := s1[k] << 1
				if k > 0 {
					l |= (s1[k-1] >> 63) & 1
				} else {
					l |= (s1[w-1] >> lastBitIdx) & 1
				}
				if k == w-1 {
					l &= lastMask
				}
				s1L[k] = l

				right := s1[k] >> 1
				if k < w-1 {
					right |= (s1[k+1] & 1) << 63
				} else {
					right |= (s1[0] & 1) << lastBitIdx
				}
				if k == w-1 {
					right &= lastMask
				}
				s1R[k] = right

				lC := c1[k] << 1
				if k > 0 {
					lC |= (c1[k-1] >> 63) & 1
				} else {
					lC |= (c1[w-1] >> lastBitIdx) & 1
				}
				if k == w-1 {
					lC &= lastMask
				}
				c1L[k] = lC

				rightC := c1[k] >> 1
				if k < w-1 {
					rightC |= (c1[k+1] & 1) << 63
				} else {
					rightC |= (c1[0] & 1) << lastBitIdx
				}
				if k == w-1 {
					rightC &= lastMask
				}
				c1R[k] = rightC
			}

			for k := 0; k < w; k++ {
				sL := s1L[k]
				sC := s1[k]
				sR := s1R[k]

				cL := c1L[k]
				cC := c1[k]
				cR := c1R[k]

				sXor := sL ^ sC
				sS := sXor ^ sR
				cS := (sL & sC) | (sXor & sR)

				cXor := cL ^ cC
				sCSum := cXor ^ cR
				cCSum := (cL & cC) | (cXor & cR)

				b0 := sS
				b1 := sCSum ^ cS
				cSc := sCSum & cS
				b2 := cCSum ^ cSc
				b3 := cCSum & cSc

				x := b0 & b1
				y := b0 | b1
				m := cur[mOff+k]

				res := (^b3) & ((x & ^b2) | (^y & b2 & m))
				if k == w-1 {
					res &= lastMask
				}
				nxt[mOff+k] = res
			}
		}
		cur, nxt = nxt, cur
	}

	simMs := int64(math.Round(float64(time.Since(t0).Nanoseconds()) / 1e6))

	alive := 0
	for _, val := range cur {
		alive += bits.OnesCount64(val)
	}

	fmt.Printf("alive=%d sim_ms=%d\n", alive, simMs)
}
