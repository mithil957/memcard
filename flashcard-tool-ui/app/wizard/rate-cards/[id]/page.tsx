"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import FlashcardRating from "@/components/flashcard-rating";
import { pb } from "@/lib/pocketbase";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Download } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface RateCardsPageProps {
  params: {
    id: string; // This is the sourceJobId
  };
}

interface FlashcardRecord {
  id: string;
  front: string;
  back: string;
  rating: string | null;
  cluster_label: number | null;
}

interface FlashcardRow {
  id: string;
  question: string;
  answer: string;
  clusterLabel: number | null;
  color: string;
  rating: number | null;
  selectedForExport: boolean;
}

const generateColorForCluster = (
  label: number | null,
  uniqueLabels: (number | null)[],
): string => {
  const index = uniqueLabels.indexOf(label);

  const medianPointUpper = Math.ceil(uniqueLabels.length / 2);
  const steps = Math.floor(index / 2);
  const mappedIndex = index % 2 === 0 ? steps : medianPointUpper + steps;

  const baseHue =
    (mappedIndex * (360.0 / Math.max(1, uniqueLabels.length))) % 360;

  return `hsl(${baseHue.toFixed(0)}, 70%, 80%)`;
};

const escapeCsvField = (field: string): string => {
  if (field === null || field === undefined) {
    return "";
  }
  const stringField = String(field);
  if (
    stringField.includes(",") ||
    stringField.includes("\n") ||
    stringField.includes('"')
  ) {
    return `"${stringField.replace(/"/g, '""')}"`;
  }
  return stringField;
};

export default function RateCardsPage({ params }: RateCardsPageProps) {
  const router = useRouter();
  const { toast } = useToast();
  const { id: sourceJobId } = params;

  const [flashcards, setFlashcards] = useState<FlashcardRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConfirmingHome, setIsConfirmingHome] = useState(false);

  const fetchCards = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    if (!pb.authStore.isValid || !pb.authStore.record?.id) {
      toast({
        title: "Authentication Error",
        description: "You must be logged in to view flashcards.",
        variant: "destructive",
      });
      router.push("/auth");
      setIsLoading(false);
      return;
    }

    try {
      const records = await pb
        .collection("flashcards_store")
        .getFullList<FlashcardRecord>({
          filter: `source_job = "${sourceJobId}" && user_id = "${pb.authStore.record?.id}"`,
          sort: "+cluster_label",
        });

      const uniqueClusterLabels = Array.from(
        new Set(records.map((r) => r.cluster_label)),
      );

      const formattedCards: FlashcardRow[] = records.map((record) => {
        const ratingValue = record.rating ? parseInt(record.rating, 10) : null;
        return {
          id: record.id,
          question: record.front,
          answer: record.back,
          clusterLabel: record.cluster_label,
          color: generateColorForCluster(
            record.cluster_label,
            uniqueClusterLabels,
          ),
          rating: isNaN(ratingValue as number) ? null : ratingValue,
          selectedForExport: true,
        };
      });

      setFlashcards(formattedCards);
    } catch (err: any) {
      console.error("Failed to load flashcards:", err);
      setError(
        "Failed to load flashcards. The job ID may be invalid, or no cards were generated/found for this job for your user.",
      );
      toast({
        title: "Error Loading Flashcards",
        description:
          err.message || "Could not retrieve flashcards for this job.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [sourceJobId, router, toast]);

  useEffect(() => {
    if (sourceJobId) {
      fetchCards();
    } else {
      setError("Job ID is missing.");
      setIsLoading(false);
    }
  }, [sourceJobId, fetchCards]);

  const handleRateCard = async (cardId: string, rating: number | null) => {
    const originalFlashcards = [...flashcards];
    setFlashcards((prev) =>
      prev.map((card) =>
        card.id === cardId ? { ...card, rating: rating } : card,
      ),
    );

    try {
      await pb.collection("flashcards_store").update(cardId, {
        rating: rating === null ? null : String(rating),
      });
      toast({
        title: "Rating Saved",
        description: `Card rating has been updated.`,
        duration: 2000,
      });
    } catch (error: any) {
      console.error("Failed to save rating:", error);
      setFlashcards(originalFlashcards); // Revert on error
      toast({
        title: "Error Saving Rating",
        description:
          error.message ||
          "Could not update the card rating. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleToggleExport = (cardId: string) => {
    setFlashcards((prev) =>
      prev.map((card) =>
        card.id === cardId
          ? { ...card, selectedForExport: !card.selectedForExport }
          : card,
      ),
    );
  };

  const handleExport = () => {
    const cardsToExport = flashcards.filter((card) => card.selectedForExport);
    if (cardsToExport.length === 0) {
      toast({
        title: "No Cards Selected",
        description: "Please select at least one card to export.",
        variant: "destructive",
      });
      return;
    }

    const csvHeader = "Front,Back\n";
    const csvRows = cardsToExport
      .map(
        (card) =>
          `${escapeCsvField(card.question)},${escapeCsvField(card.answer)}`,
      )
      .join("\n");
    const csvContent = csvHeader + csvRows;

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `flashcards_job_${sourceJobId}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast({
      title: "Export Successful",
      description: "Selected flashcards have been exported as CSV.",
    });
  };

  const handleGoHomeConfirmed = () => {
    setIsConfirmingHome(false);
    router.push("/actions"); // Navigate to main actions page
  };

  const handleBackToJobs = () => {
    router.push("/jobstat");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
        <Card className="w-full max-w-4xl bg-white rounded-3xl shadow-lg p-6 text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <h2 className="text-3xl font-bold mb-6">Loading flashcards...</h2>
          <p className="text-gray-600">
            Please wait while we load your flashcards.
          </p>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
        <Card className="w-full max-w-4xl bg-white rounded-3xl shadow-lg p-6 text-center">
          <h2 className="text-3xl font-bold mb-6 text-red-600">Error</h2>
          <p className="text-red-500 mb-6">{error}</p>
          <Button onClick={handleBackToJobs} className="">
            Back to Jobs List
          </Button>
        </Card>
      </div>
    );
  }

  if (!isLoading && flashcards.length === 0) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
        <Card className="w-full max-w-4xl bg-white rounded-3xl shadow-lg p-6 text-center">
          <h2 className="text-3xl font-bold mb-6">No Flashcards Found</h2>
          <p className="text-gray-600 mb-6">
            No flashcards were found for this job, or they might still be
            processing.
          </p>
          <Button onClick={handleBackToJobs} className="">
            Back to Jobs List
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
      <Card className="w-full max-w-5xl bg-[#FAF9F7] rounded-3xl shadow-lg overflow-hidden">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-semibold">
              Rate and Export Flashcards
              <p className="text-base font-light text-gray-600 mb-0">
                This is to rate the quality of the cards generated
              </p>
              <p className="text-base font-light text-gray-600 mb-0">
                {flashcards.length} {flashcards.length == 1 ? "card" : "cards"}
              </p>
            </h1>
            <AlertDialog
              open={isConfirmingHome}
              onOpenChange={setIsConfirmingHome}
            >
              <AlertDialogTrigger asChild>
                <Button variant="outline" className="font-semibold text-base">
                  Home
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Confirm Navigation</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to return to the home page? Your
                    ratings are saved as you make them, but ensure all desired
                    actions are complete.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleGoHomeConfirmed}>
                    Confirm
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>

          <div className="border rounded-lg overflow-x-auto mb-6">
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-100">
                  <TableHead className="font-bold w-16 text-center">
                    Group
                  </TableHead>
                  <TableHead className="font-bold min-w-[200px]">
                    Front
                  </TableHead>
                  <TableHead className="font-bold min-w-[200px]">
                    Back
                  </TableHead>
                  <TableHead className="font-bold w-[200px] text-center">
                    Rating
                  </TableHead>
                  <TableHead className="font-bold w-20 text-center">
                    Export
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {flashcards.map((card) => (
                  <TableRow key={card.id} className="border-t hover:bg-gray-50">
                    <TableCell className="align-middle text-center">
                      <div
                        className="w-6 h-6 rounded-sm mx-auto"
                        style={{ backgroundColor: card.color }}
                        title={card.clusterLabel?.toString() || "No Cluster"}
                      ></div>
                    </TableCell>
                    <TableCell className="align-middle py-3 px-4 text-base">
                      {card.question}
                    </TableCell>
                    <TableCell className="align-middle py-3 px-4 text-base">
                      {card.answer}
                    </TableCell>
                    <TableCell className="align-middle text-center py-3">
                      <FlashcardRating
                        cardId={card.id}
                        currentRating={card.rating}
                        onRate={handleRateCard}
                      />
                    </TableCell>
                    <TableCell className="align-middle text-center py-3">
                      <Checkbox
                        checked={card.selectedForExport}
                        onCheckedChange={() => handleToggleExport(card.id)}
                        aria-label={`Select card ${card.id} for export`}
                        className="mx-auto"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <Button
              variant="outline"
              onClick={handleBackToJobs}
              className="font-semibold text-base w-full sm:w-auto"
            >
              Back to Jobs
            </Button>
            <Button
              onClick={handleExport}
              className="font-semibold text-base bg-blue-600 hover:bg-blue-700 text-white w-full sm:w-auto"
            >
              <Download className="mr-2 h-4 w-4" />
              Export Selected to CSV
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
