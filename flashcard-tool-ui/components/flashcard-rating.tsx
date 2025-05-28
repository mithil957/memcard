"use client";
import { X } from "lucide-react";

interface FlashcardRatingProps {
  cardId: string;
  currentRating: number | null;
  onRate: (cardId: string, rating: number | null) => void;
}

export default function FlashcardRating({
  cardId,
  currentRating,
  onRate,
}: FlashcardRatingProps) {
  const emojis = [
    { rating: 1, emoji: "😩", label: "Terrible" },
    { rating: 2, emoji: "😔", label: "Poor" },
    { rating: 3, emoji: "😐", label: "Okay" },
    { rating: 4, emoji: "🙂", label: "Good" },
    { rating: 5, emoji: "💯", label: "Great" },
    { rating: 6, emoji: "😵‍💫", label: "Confusing" },
    { rating: 7, emoji: "🤬", label: "Inaccurate" },
  ];

  return (
    <div className="flex items-center justify-center space-x-4">
      {emojis.map((emoji) => (
        <button
          key={emoji.rating}
          onClick={() => onRate(cardId, emoji.rating)}
          className={`text-2xl transition-transform ${
            currentRating === emoji.rating
              ? "scale-150"
              : "scale-100 hover:scale-150"
          }`}
          aria-label={`Rate as ${emoji.label}`}
        >
          {emoji.emoji}
        </button>
      ))}
    </div>
  );
}
