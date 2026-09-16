{-# OPTIONS --safe #-}
module Section1_CorrectionB.CorrectionB where

open import Data.Rational
open import Data.Nat using (ℕ)

postulate π : ℚ
postulate sqrt3 : ℚ

b-correction : ℚ
b-correction = π ÷ (4 * π * π + 2 * π * sqrt3)

postulate b-pos : b-correction > 0ℚ
postulate b-lt-one : b-correction < 1ℚ
