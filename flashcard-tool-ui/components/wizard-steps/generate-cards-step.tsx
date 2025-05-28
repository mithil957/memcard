"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { pb } from "@/lib/pocketbase";
import { useToast } from "@/hooks/use-toast";

interface GenerateCardsStepProps {
  selectedFile: File | null;
  sourcePdfRecordId: string | null;
  uploadPdfFile: (file: File) => Promise<string | null>;
  setUploadedPdfRecordId: (id: string | null) => void;
}

export default function GenerateCardsStep({
  selectedFile,
  sourcePdfRecordId,
  uploadPdfFile,
  setUploadedPdfRecordId,
}: GenerateCardsStepProps) {
  const [isJobQueued, setIsJobQueued] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<{
    success: boolean;
    message: React.ReactNode;
    jobId?: string;
  } | null>(null);
  const router = useRouter();
  const { toast } = useToast();

  const handleGenerateCards = async () => {
    setIsProcessing(true);
    setResult(null);

    if (!pb.authStore.isValid || !pb.authStore.record?.id) {
      toast({
        title: "Authentication Error",
        description: "You must be logged in to generate flashcards.",
        variant: "destructive",
      });
      setIsProcessing(false);
      router.push("/auth");
      return;
    }

    let currentPdfId = sourcePdfRecordId;

    if (!currentPdfId && selectedFile) {
      const newPdfId = await uploadPdfFile(selectedFile);
      if (newPdfId) {
        setUploadedPdfRecordId(newPdfId);
        currentPdfId = newPdfId;
      } else {
        setIsProcessing(false);
        return;
      }
    }

    if (!currentPdfId) {
      toast({
        title: "Error",
        description:
          "PDF is missing. Please select and upload a PDF before generating cards.",
        variant: "destructive",
      });
      setIsProcessing(false);
      return;
    }

    const userId = pb.authStore.record.id;

    try {
      const jobData = {
        user: userId,
        source_pdf: currentPdfId,
        status: "Queued",
      };

      const newJobRecord = await pb.collection("job_requests").create(jobData);

      setResult({
        success: true,
        message: "Job queued successfully! Redirecting to job status...",
        jobId: newJobRecord.id,
      });
      setIsJobQueued(true);
      toast({
        title: "Job Queued",
        description: "Flashcard generation has started. Redirecting...",
      });
      router.push("/jobstat");
    } catch (error: any) {
      console.error("Job Creation Error:", error);
      let errorMessage = "An unexpected error occurred while creating the job.";
      if (error.data && error.data.message) {
        errorMessage = error.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }

      setResult({
        success: false,
        message: errorMessage,
      });
      setIsJobQueued(false);
      toast({
        title: "Job Creation Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="py-4 h-full flex flex-col">
      <h2 className="text-3xl font-semibold mb-4">Generate Cards</h2>

      <div className="space-y-6 mb-6">
        <Card className="p-4">
          <div className="flex items-start space-x-3">
            <FileText className="h-5 w-5 mt-0.5 text-blue-600" />
            <div>
              <h3 className="font-bold tracking-tight">Source PDF</h3>
              <p className="text-base font-light text-gray-600">
                {selectedFile
                  ? selectedFile.name
                  : sourcePdfRecordId
                    ? "Previously uploaded PDF"
                    : "No PDF selected"}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {result && (
        <Alert
          className={`mb-6 ${result.success ? "border-green-500 text-green-800" : "border-red-500 text-red-800"}`}
        >
          {result.success ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertCircle className="h-4 w-4 text-red-600" />
          )}
          <AlertTitle className="font-semibold">
            {result.success ? "Job Queued" : "Error"}
          </AlertTitle>
          <AlertDescription className="text-sm">
            {result.message}
          </AlertDescription>
        </Alert>
      )}

      <div className="mt-auto">
        {!isJobQueued ? (
          <Button
            onClick={handleGenerateCards}
            disabled={isProcessing || (!selectedFile && !sourcePdfRecordId)}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white text-xl font-medium py-5 h-auto"
          >
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              "Generate Flashcards"
            )}
          </Button>
        ) : (
          <div className="text-center text-gray-600">
            Redirecting to job status...
          </div>
        )}
      </div>
    </div>
  );
}
