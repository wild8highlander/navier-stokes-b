{-# OPTIONS --safe #-}
module Section4_KdV.KdV where

open import Data.Float

soliton : Float -> Float -> Float -> Float
soliton c x t = (c / 2.0) * (1.0 / cosh (sqrt c / 2.0 * (x - c * t))) ^ 2.0
