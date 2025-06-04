"use client";

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
    { rating: 5, emoji: "💯", label: "Perfect" }, // Perfect
    { rating: 4, emoji: "😐", label: "Okay" }, // Mid
    { rating: 1, emoji: "😩", label: "Terrible" }, // Terrible
    { rating: 6, emoji: "😵‍💫", label: "Confusing" }, // Confusing
    { rating: 7, emoji: "🤬", label: "Inaccurate" }, // Inaccurate
  ];

  return (
    <div className="flex items-center justify-center space-x-2 sm:space-x-3">
      {emojis.map((emoji) => (
        <button
          key={emoji.rating}
          onClick={() => onRate(cardId, emoji.rating)}
          className={`text-xl sm:text-2xl transition-transform ${
            currentRating === emoji.rating
              ? "scale-125 sm:scale-150"
              : "scale-100 hover:scale-150 sm:hover:scale-150"
          }`}
          aria-label={`Rate as ${emoji.label}`}
          title={emoji.label}
        >
          {emoji.emoji}
        </button>
      ))}
    </div>
  );
}
