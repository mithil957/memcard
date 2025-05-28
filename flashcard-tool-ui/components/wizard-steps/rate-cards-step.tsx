"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, RotateCw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import FlashcardRating from "@/components/flashcard-rating";
import { cn } from "@/lib/utils";
import { pb } from "@/lib/pocketbase";
import { useToast } from "@/hooks/use-toast";

interface RateCardsStepProps {
  flashcards: Array<{ question: string; answer: string; id: string }>;
  ratings: Record<string, number | null>;
  setRatings: (ratings: Record<string, number | null>) => void;
}

export default function RateCardsStep({
  flashcards,
  ratings,
  setRatings,
}: RateCardsStepProps) {
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const { toast } = useToast();

  const handlePrevCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(currentCardIndex - 1);
      setIsFlipped(false);
    }
  };

  const handleNextCard = () => {
    if (currentCardIndex < flashcards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1);
      setIsFlipped(false);
    }
  };

  const handleFlipCard = () => {
    setIsFlipped(!isFlipped);
  };

  const handleRateCard = async (cardId: string, rating: number | null) => {
    const prevRating = ratings[cardId];

    setRatings({
      ...ratings,
      [cardId]: rating,
    });

    try {
      const dataToUpdate = {
        rating: rating === null ? null : String(rating),
      };
      await pb.collection("flashcards_store").update(cardId, dataToUpdate);
      toast({
        title: "Rating Saved",
        description: `Card rating has been updated.`,
        duration: 2000,
      });
    } catch (error: any) {
      console.error("Failed to save rating:", error);
      toast({
        title: "Error Saving Rating",
        description:
          error.message ||
          "Could not update the card rating. Please try again.",
        variant: "destructive",
      });

      setRatings({
        ...ratings,
        [cardId]: prevRating,
      });
    }
  };

  const currentCard = flashcards[currentCardIndex];

  return (
    <div className="py-4 h-full flex flex-col">
      <h2 className="text-3xl font-semibold mb-1">Rate cards</h2>
      <p className="text-base font-light text-gray-600 mb-0">
        This is to rate the quality of the cards generated
      </p>

      <div className="relative mt-4 mb-5 flex flex-col flex-grow flashcard-container">
        <Card
          className={cn(
            "border rounded-lg flex-grow",
            "flashcard",
            isFlipped ? "flipped" : "",
          )}
        >
          <div className="flashcard-front p-8 flex items-center justify-center h-full w-full">
            <p className="text-xl text-center">{currentCard.question}</p>
          </div>
          <div className="flashcard-back p-8 flex items-center justify-center h-full w-full">
            <p className="text-xl text-center">{currentCard.answer}</p>
          </div>
        </Card>

        <div className="absolute left-0 top-1/2 -translate-y-1/2">
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePrevCard}
            disabled={currentCardIndex === 0}
            className="h-8 w-8"
          >
            <ChevronLeft className="h-3 w-3" />
          </Button>
        </div>

        <div className="absolute right-0 top-1/2 -translate-y-1/2">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleNextCard}
            disabled={currentCardIndex === flashcards.length - 1}
            className="h-8 w-8"
          >
            <ChevronRight className="h-3 w-3" />
          </Button>
        </div>

        <Button
          variant="outline"
          onClick={(e) => {
            e.stopPropagation();
            handleFlipCard();
          }}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 bg-white hover:bg-gray-100"
          aria-label="Flip card"
        >
          <RotateCw className="mr-2 h-4 w-4" /> Flip
        </Button>
      </div>

      <div className="flex flex-col items-center ">
        <FlashcardRating
          cardId={currentCard.id}
          currentRating={ratings[currentCard.id]}
          onRate={handleRateCard}
        />

        <div className="flex justify-between w-full mt-0">
          <div className="text-sm text-gray-500">
            Card {currentCardIndex + 1} of {flashcards.length}
          </div>
        </div>
      </div>
    </div>
  );
}
