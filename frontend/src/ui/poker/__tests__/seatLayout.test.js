import { describe, it, expect } from 'vitest'
import { seatPositions, HERO_SLOT } from '../seatLayout.ts'

describe('where the seats go', () => {
  it('gives every seat its own chair, whatever the ids happen to be', () => {
    // A seat id here is a room_player row, not a chair number: 860 and 862 are
    // "two apart" in name only, and the arithmetic that assumed otherwise put
    // the opponent in the hero's chair.
    const positions = seatPositions([860, 862], 860, 2)
    expect(positions[860]).toEqual(HERO_SLOT)
    expect(positions[862]).not.toEqual(HERO_SLOT)
  })

  it('puts me at the bottom and the rest around the table, four handed', () => {
    const positions = seatPositions([41, 55, 63, 70], 55, 4)
    expect(positions[55]).toEqual(HERO_SLOT)
    const others = [positions[63], positions[70], positions[41]]
    expect(new Set(others.map((slot) => `${slot.x},${slot.y}`)).size).toBe(3)
    expect(others.filter((slot) => slot.x < 35)).toHaveLength(1)
    expect(others.filter((slot) => slot.x > 65)).toHaveLength(1)
  })

  it('leaves the hero chair empty for somebody only watching', () => {
    const positions = seatPositions([12, 19], 99, 2)
    expect(Object.values(positions)).not.toContainEqual(HERO_SLOT)
  })
})
