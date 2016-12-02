; showimg.s
;
; Minimal C64 assembly program to load and
; display a multi-colour bitmap image.
;
; It expects the image data to begin
; immediatly after the end of the code.
;
; $ xa -o showimg.prg showimg.s
;
; - Philip Heron <phil@sanslogic.co.uk>

	; PRG header
	.byte $01
	.byte $08

* = $0801
	; BASIC startup (2061 SYS2061)
	.byte $0C,$08
	.word _start
	.byte $9E
	.byte $32,$30,$36,$31
	.byte $00,$00,$00

_vic_bitmap = $6000
_vic_screen = $4400
_vic_colour = $D800

_start	sei
	
	; Copy the bitmap data (the src+dst pointers are already setup)
	ldx #$40
	ldy #$1F
	jsr _memcpy
	
	; Copy the screen data
	lda #<_vic_screen
	sta _memcpy_dst
	lda #>_vic_screen
	sta _memcpy_dst+1
	
	ldx #$E8
	ldy #$03
	jsr _memcpy
	
	; Copy the colour data
	lda #<_vic_colour
	sta _memcpy_dst
	lda #>_vic_colour
	sta _memcpy_dst+1
	
	ldx #$E8
	ldy #$03
	jsr _memcpy
	
	; Configure VIC for multi-colour bitmap mode
	lda #%00011100
	sta $D018
	
	lda #%00111011
	sta $D011
	
	lda #%00011000
	sta $D016
	
	; Remap VIC-II to $4000-$7FFF
	lda #%00000010
	sta $DD00
	
	; Set border and background to the same colour
	lda #0		; This value gets overwritten
	sta $D020
	sta $D021
	
_il	jmp _il

; Copy X*Y bytes from _memcpy_src to _memcpy_dst
_memcpy	inx
	iny
_loop	dex
	bne _cp
	dey
	bne _cp
	rts
_cp	lda _image
	sta _vic_bitmap
	inc _memcpy_src
	bne _ncs
	inc _memcpy_src+1
_ncs	inc _memcpy_dst
	bne _ncd
	inc _memcpy_dst+1
_ncd	jmp _loop

_memcpy_src = _cp+1
_memcpy_dst = _cp+4

_image

