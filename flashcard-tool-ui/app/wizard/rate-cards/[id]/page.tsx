"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StepperUI from "@/components/stepper-ui";
import RateCardsStep from "@/components/wizard-steps/rate-cards-step";
import ExportStep from "@/components/wizard-steps/export-step";
import { pb } from "@/lib/pocketbase"; // Import Pocketbase
import { useToast } from "@/hooks/use-toast"; // For potential error toasts
import { Loader2 } from "lucide-react"; // For loading indicator
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
    id: string;
  };
}

interface FlashcardRecord {
  id: string;
  front: string;
  back: string;
}

export default function RateCardsPage({ params }: RateCardsPageProps) {
  const router = useRouter();
  const { toast } = useToast();
  const { id: sourceJobId } = params;
  const [currentStep, setCurrentStep] = useState(1);
  const [flashcards, setFlashcards] = useState<
    Array<{ question: string; answer: string; id: string }>
  >([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ratings, setRatings] = useState<Record<string, number | null>>({});
  const [isConfirmingHome, setIsConfirmingHome] = useState(false);

  // Updated steps for the two-step wizard
  const steps = [
    { number: 1, label: "Rate cards" },
    { number: 2, label: "Export" },
  ];

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep == 1) {
      router.push("/jobstat");
    } else {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleGoHomeConfirmed = () => {
    setIsConfirmingHome(false);
    router.push("/actions");
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <RateCardsStep
            flashcards={flashcards}
            ratings={ratings}
            setRatings={setRatings}
          />
        );
      case 2:
        return <ExportStep flashcards={flashcards} />;
      default:
        return (
          <RateCardsStep
            flashcards={flashcards}
            ratings={ratings}
            setRatings={setRatings}
          />
        );
    }
  };

  useEffect(() => {
    const fetchCards = async () => {
      setIsLoading(true);
      setError(null);

      if (!pb.authStore.isValid || !pb.authStore.model?.id) {
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
            filter: `source_job = "${sourceJobId}" && user_id = "${pb.authStore.model.id}"`,
          });

        const formattedCards = records.map((record) => ({
          id: record.id,
          question: record.front,
          answer: record.back,
        }));

        setFlashcards(formattedCards);

        const initialRatings: Record<string, number | null> = {};
        formattedCards.forEach((card) => {
          initialRatings[card.id] = null;
        });
        setRatings(initialRatings);
      } catch (err: any) {
        console.error("Failed to load flashcards:", err);
        setError(
          "Failed to load flashcards. The job ID may be invalid, or no cards were generated for this job.",
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
    };

    if (sourceJobId) {
      fetchCards();
    } else {
      setError("Job ID is missing.");
      setIsLoading(false);
    }
  }, [sourceJobId, router, toast]);

  // const handleFinishRating = () => {
  //   // This function's purpose might change.
  //   // If ratings are saved to backend, this would be the place.
  //   console.log("Submitting ratings:", ratings);
  //   // For now, it's just a placeholder.
  // };

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
          <Button onClick={() => router.push("/jobstat")} className="">
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
          <h2 className="text-3xl font-bold mb-6">No flashcards found</h2>
          <p className="text-gray-600 mb-6">
            No flashcards were found for this job, or they might still be
            processing.
          </p>
          <Button onClick={() => router.push("/jobstat")} className="">
            Back to Jobs List
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl bg-[#FAF9F7] rounded-3xl shadow-lg overflow-hidden relative">
        <div className="pr-6 pl-6">
          <div className="flex flex-col md:flex-row gap-6">
            <div className="md:w-1/3 relative pb-6 min-h-[600px]">
              <StepperUI steps={steps} currentStep={currentStep} />
              <div className="hidden md:block absolute top-0 right-0 bottom-0 w-px bg-[#C6D5EB]"></div>
            </div>

            <div className="md:w-2/3 flex flex-col">
              <div className="p-4 pb-16 flex-grow">{renderStep()}</div>

              <div className="absolute bottom-6 right-10 flex justify-end mt-6 space-x-2">
                <Button
                  variant="outline"
                  onClick={handleBack}
                  className="font-semibold text-base"
                >
                  Back
                </Button>

                {currentStep === 1 && (
                  <Button
                    onClick={handleNext}
                    className="font-semibold text-base"
                  >
                    Next
                  </Button>
                )}

                {currentStep === 2 && ( // Show Home button on Export step
                  <AlertDialog
                    open={isConfirmingHome}
                    onOpenChange={setIsConfirmingHome}
                  >
                    <AlertDialogTrigger asChild>
                      <Button className="font-semibold text-base">Home</Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Confirm Navigation</AlertDialogTitle>
                        <AlertDialogDescription>
                          Are you sure you want to return to the wizard home
                          page? Your ratings might not be saved if you haven't
                          submitted them.
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
                )}
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
