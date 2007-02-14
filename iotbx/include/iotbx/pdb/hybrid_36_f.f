C Fortran 77 port of the hy36encode() and hy36decode() functions in the
C hybrid_36.py Python prototype/reference implementation.
C See the Python script for more information.
C
C This file has no external dependencies.
C To use in your project, comment out "program exercise" at the
C bottom.
C
C This file is unrestricted Open Source (cctbx.sf.net).
C Please send corrections and enhancements to cctbx@cci.lbl.gov .
C
C Ralf W. Grosse-Kunstleve, Feb 2007.

      subroutine encode_pure(
     &  digits,
     &  digits_size,
     &  value,
     &  result,
     &  diag,
     &  diag_size)
      implicit none
C Input
      character digits*(*)
      integer digits_size
      integer value
C Output
      character result*(*)
      character diag*(*)
      integer diag_size
C Local
      character buf*16
      integer i, j, rest, val
C
      val = value
      if (val .lt. 0) then
        diag = 'value out of range.'
        diag_size = 19
        return
      endif
      if (val .eq. 0) then
        result = digits(1:1)
        diag_size = 0
        return
      endif
      i = 0
    1 continue
        rest = val / digits_size
        j = val - rest * digits_size + 1
        i = i + 1
        buf(i:i) = digits(j:j)
        val = rest
        if (val .ne. 0) goto 1
      j = 1
    2 continue
        result(j:j) = buf(i:i)
        i = i - 1
        j = j + 1
        if (i .gt. 0) goto 2
      result(j:) = ' '
      diag_size = 0
      return
      end

      subroutine decode_pure(
     &  digits_values,
     &  digits_size,
     &  s,
     &  s_size,
     &  result,
     &  diag,
     &  diag_size)
      implicit none
C Input
      integer digits_values(0:*)
      integer digits_size
      character s*(*)
      integer s_size
C Output
      integer result
      character diag*(*)
      integer diag_size
C Local
      integer si, dv
      integer value
      integer i
C
      value = 0
      do 1 i=1,s_size
        value = value * digits_size
        si = ichar(s(i:i))
        if (si .lt. 0 .or. si .gt. 127) then
          diag = 'invalid number literal.'
          diag_size = 23
          return
        endif
        dv = digits_values(si)
        if (dv .lt. 0) then
          diag = 'invalid number literal.'
          diag_size = 23
          return
        endif
        value = value + dv
    1 continue
      result = value
      diag_size = 0
      return
      end

      subroutine hy36encode(
     &  width,
     &  value,
     &  result,
     &  diag,
     &  diag_size)
      implicit none
C Input
      integer width
      integer value
C Output
      character result*(*)
      character diag*(*)
      integer diag_size
C Local
      character digits_upper*36
      character digits_lower*36
      data digits_upper /'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'/
      data digits_lower /'0123456789abcdefghijklmnopqrstuvwxyz'/
      save digits_upper
      save digits_lower
      integer i
C
      i = value
      if (width .eq. 4) then
        if (i .ge. -999) then
          if (i .lt. 10000) then
            write(result, '(I4)') i
            diag_size = 0
            return
          endif
          i = i - 10000
          if (i .lt. 1213056) then
            i = i + 466560
            call encode_pure(
     &        digits_upper, 36, i, result, diag, diag_size)
            return
          endif
          i = i - 1213056
          if (i .lt. 1213056) then
            i = i + 466560
            call encode_pure(
     &        digits_lower, 36, i, result, diag, diag_size)
            return
          endif
        endif
      else if (width .eq. 5) then
        if (i .ge. -9999) then
          if (i .lt. 100000) then
            write(result, '(I5)') i
            diag_size = 0
            return
          endif
          i = i - 100000
          if (i .lt. 43670016) then
            i = i + 16796160
            call encode_pure(
     &        digits_upper, 36, i, result, diag, diag_size)
            return
          endif
          i = i - 43670016
          if (i .lt. 43670016) then
            i = i + 16796160
            call encode_pure(
     &        digits_lower, 36, i, result, diag, diag_size)
            return
          endif
        endif
      else
        diag = 'unsupported width.'
        diag_size = 18
        return
      endif
      diag = 'value out of range.'
      diag_size = 19
      return
      end

      subroutine hy36decode(
     &  width,
     &  s,
     &  s_size,
     &  result,
     &  diag,
     &  diag_size)
      implicit none
C Input
      integer width
      character s*(*)
      integer s_size
C Output
      integer result
      character diag*(*)
      integer diag_size
C Local
      character digits_upper*36
      character digits_lower*36
      data digits_upper /'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'/
      data digits_lower /'0123456789abcdefghijklmnopqrstuvwxyz'/
      save digits_upper
      save digits_lower
      logical first_call
      integer digits_values_upper(0:127)
      integer digits_values_lower(0:127)
      save first_call
      save digits_values_upper
      save digits_values_lower
      data first_call /.true./
      data digits_values_upper /128*-1/
      data digits_values_lower /128*-1/
      character ie_range*57
      save ie_range
      data ie_range /
     &  'internal error hy36decode: integer value out of range.'/
      integer i, di
C
      if (first_call) then
        first_call = .false.
        do 1, i=1,36
          di = ichar(digits_upper(i:i))
          if (di .lt. 0 .or. di .gt. 127) then
            diag = ie_range
            diag_size = len(ie_range)
            return
          endif
          digits_values_upper(di) = i-1
    1   continue
        do 2, i=1,36
          di = ichar(digits_lower(i:i))
          if (di .lt. 0 .or. di .gt. 127) then
            diag = ie_range
            diag_size = len(ie_range)
            return
          endif
          digits_values_lower(di) = i-1
    2   continue
      endif
      if (s_size .eq. width) then
        di = ichar(s(1:1))
        if (di .ge. 0 .and. di .le. 127) then
          if (digits_values_upper(di) .ge. 10) then
            call decode_pure(
     &        digits_values_upper, 36, s, s_size,
     &        result, diag, diag_size)
            if (diag_size .ne. 0) return
            if (width .eq. 4) then
C                             - 10*36**(width-1) + 10**width
              result = result - 456560
              diag_size = 0
            else if (width .eq. 5) then
              result = result - 16696160
              diag_size = 0
            else
              diag = 'unsupported width.'
              diag_size = 18
            endif
            return
          else if (digits_values_lower(di) .ge. 10) then
            call decode_pure(
     &        digits_values_lower, 36, s, s_size,
     &        result, diag, diag_size)
            if (diag_size .ne. 0) return
            if (width .eq. 4) then
C                             + 16*36**(width-1) + 10**width
              result = result + 756496
              diag_size = 0
            else if (width .eq. 5) then
              result = result + 26973856
              diag_size = 0
            else
              diag = 'unsupported width.'
              diag_size = 18
            endif
            return
          else
            if (width .eq. 4) then
              read(s, '(I4)', err=3) result
              diag_size = 0
            else if (width .eq. 5) then
              read(s, '(I5)', err=3) result
              diag_size = 0
            else
              diag = 'unsupported width.'
              diag_size = 18
            endif
            return
          endif
        endif
      endif
    3 diag = 'invalid number literal.'
      diag_size = 23
      return
      end

      subroutine tst_hybrid_36_f(quick)
      implicit none
C Input
      logical quick
C Local
      integer value
      character diag*128
      integer diag_size
      character s*16
      integer decoded
C
      call hy36decode(4, '    ', 4, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode empty'
      if (decoded .ne. 0) stop 'error decoded value empty'
      call hy36decode(4, '  -0', 4, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode empty'
      if (decoded .ne. 0) stop 'error decoded value -0'
      call hy36decode(4, '-999', 4, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode -999'
      if (decoded .ne. -999) stop 'error decoded value -999'
      call hy36decode(4, '9999', 4, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode 9999'
      if (decoded .ne. 9999) stop 'error decoded value 9999'
      call hy36decode(4, 'A000', 4, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode A000'
      if (decoded .ne. 10000) stop 'error decoded value A000'
      call hy36decode(4, 'ZZZZ', 4, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode ZZZZ'
      if (decoded .ne. 1223055) stop 'error decoded value ZZZZ'
      call hy36decode(4, 'a000', 4, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode a000'
      if (decoded .ne. 1223056) stop 'error decoded value a000'
      call hy36decode(4, 'zzzz', 4, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode zzzz'
      if (decoded .ne. 2436111) stop 'error decoded value zzzz'
C
      call hy36decode(5, '     ', 5, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode empty'
      if (decoded .ne. 0) stop 'error decoded value empty'
      call hy36decode(5, '   -0', 5, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode empty'
      if (decoded .ne. 0) stop 'error decoded value -0'
      call hy36decode(5, '-9999', 5, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode -9999'
      if (decoded .ne. -9999) stop 'error decoded value -9999'
      call hy36decode(5, '99999', 5, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode 99999'
      if (decoded .ne. 99999) stop 'error decoded value 99999'
      call hy36decode(5, 'A0000', 5, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode A0000'
      if (decoded .ne. 100000) stop 'error decoded value A0000'
      call hy36decode(5, 'ZZZZZ', 5, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode ZZZZZ'
      if (decoded .ne. 43770015) stop 'error decoded value ZZZZZ'
      call hy36decode(5, 'a0000', 5, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode a0000'
      if (decoded .ne. 43770016) stop 'error decoded value a0000'
      call hy36decode(5, 'zzzzz', 5, decoded, diag, diag_size)
      if (diag_size .ne. 0) stop 'error hy36decode zzzzz'
      if (decoded .ne. 87440031) stop 'error decoded value zzzzz'
C
      if (.not. quick) then
        do 1, value=-999,2436111
          diag_size = -1
          call hy36encode(4, value, s, diag, diag_size)
          if (diag_size .ne. 0) stop 'error hy36encode'
          decoded = -1000
          diag_size = -1
          call hy36decode(4, s, 4, decoded, diag, diag_size)
          if (diag_size .ne. 0) stop 'error hy36decode'
          if (decoded .ne. value) stop 'error decoded value'
    1   continue
C
        do 2, value=-9999,110000
          diag_size = -1
          call hy36encode(5, value, s, diag, diag_size)
          if (diag_size .ne. 0) stop 'error hy36encode'
          decoded = -10000
          diag_size = -1
          call hy36decode(5, s, 5, decoded, diag, diag_size)
          if (diag_size .ne. 0) stop 'error hy36decode'
          if (decoded .ne. value) stop 'error decoded value'
    2   continue
      endif
C
      call hy36encode(4, -1000, s, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36encode range'
      if (diag .ne. 'value out of range.') stop 'error diag range'
      call hy36encode(4, 2436112, s, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36encode range'
      if (diag .ne. 'value out of range.') stop 'error diag range'
      call hy36decode(4, ' abc', 4, decoded, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36decode invalid'
      if (diag .ne. 'invalid number literal.') stop 'error diag invalid'
      call hy36decode(4, 'abc-', 4, decoded, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36decode invalid'
      if (diag .ne. 'invalid number literal.') stop 'error diag invalid'
      call hy36decode(4, 'A=BC', 4, decoded, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36decode invalid'
      if (diag .ne. 'invalid number literal.') stop 'error diag invalid'
C
      call hy36encode(5, -10000, s, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36encode range'
      if (diag .ne. 'value out of range.') stop 'error diag range'
      call hy36encode(5, 87440032, s, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36encode range'
      if (diag .ne. 'value out of range.') stop 'error diag range'
      call hy36decode(5, ' abcd', 5, decoded, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36decode invalid'
      if (diag .ne. 'invalid number literal.') stop 'error diag invalid'
      call hy36decode(5, 'ABCD-', 5, decoded, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36decode invalid'
      if (diag .ne. 'invalid number literal.') stop 'error diag invalid'
      call hy36decode(5, 'a=bcd', 5, decoded, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36decode invalid'
      if (diag .ne. 'invalid number literal.') stop 'error diag invalid'
C
      call hy36encode(3, 0, s, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36encode width'
      if (diag .ne. 'unsupported width.') stop 'error diag width'
      call hy36decode(3, '  0', 3, decoded, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36decode width'
      if (diag .ne. 'unsupported width.') stop 'error diag width'
      call hy36decode(3, 'A00', 3, decoded, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36decode width'
      if (diag .ne. 'unsupported width.') stop 'error diag width'
      call hy36decode(3, 'a00', 3, decoded, diag, diag_size)
      if (diag_size .eq. 0) stop 'error hy36decode width'
      if (diag .ne. 'unsupported width.') stop 'error diag width'
C
      return
      end

      program exercise
      call tst_hybrid_36_f(.false.)
      end
