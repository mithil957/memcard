"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StepperUI from "@/components/stepper-ui";
import SelectPDFStep from "@/components/wizard-steps/select-pdf-step";
import GenerateCardsStep from "@/components/wizard-steps/generate-cards-step";
import { pb } from "@/lib/pocketbase";
import { useToast } from "@/hooks/use-toast";
export default function WizardPage() {
  const { toast } = useToast();
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedPdfRecordId, setUploadedPdfRecordId] = useState<string | null>(
    null,
  );

  const steps = [
    { number: 1, label: "Select PDF" },
    { number: 2, label: "Generate Cards" },
  ];

  const handleFileSelect = (file: File | null) => {
    setSelectedFile(file);
    setUploadedPdfRecordId(null);
  };

  const uploadPdfFile = async (fileToUpload: File): Promise<string | null> => {
    if (!pb.authStore.isValid || !pb.authStore.record?.id) {
      toast({
        title: "Authentication Error",
        description: "You must be logged in to upload a PDF.",
        variant: "destructive",
      });
      router.push("/auth");
      return null;
    }

    try {
      const formData = new FormData();
      formData.append("pdf_document", fileToUpload);
      formData.append("user", pb.authStore.record.id);
      formData.append("original_filename", fileToUpload.name);
      formData.append("file_size", fileToUpload.size.toString());

      const record = await pb.collection("user_pdfs").create(formData);
      toast({
        title: "PDF Uploaded",
        description: `${fileToUpload.name} has been uploaded successfully.`,
      });
      return record.id;
    } catch (error: any) {
      console.error("PDF Upload Error:", error);
      toast({
        title: "PDF Upload Failed",
        description:
          error.message || "Could not upload the PDF. Please try again.",
        variant: "destructive",
      });
      return null;
    }
  };

  const handleNext = async () => {
    if (currentStep === 1) {
      // PDF upload is deferred to GenerateCardsStep
      if (selectedFile) {
        setCurrentStep(currentStep + 1);
      } else {
        toast({
          title: "No PDF Selected",
          description: "Please select a PDF file to continue.",
          variant: "destructive",
        });
      }
    } else if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep === 1) {
      router.push("/actions");
    } else {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <SelectPDFStep
            onFileSelect={handleFileSelect}
            selectedFile={selectedFile}
          />
        );
      case 2:
        return (
          <GenerateCardsStep
            selectedFile={selectedFile}
            sourcePdfRecordId={uploadedPdfRecordId}
            uploadPdfFile={uploadPdfFile} // Pass the upload function
            setUploadedPdfRecordId={setUploadedPdfRecordId} // Pass the setter
          />
        );
      default:
        return (
          <SelectPDFStep
            onFileSelect={handleFileSelect}
            selectedFile={selectedFile}
          />
        );
    }
  };

  const isNextDisabled = currentStep === 1 && !selectedFile;

  const getNextButtonText = () => {
    // Simplified, as upload is deferred
    return "Next";
  };
  const showNextButton = currentStep < steps.length && currentStep !== 2;

  return (
    <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl bg-[#FAF9F7] rounded-3xl shadow-lg overflow-hidden relative">
        <div className="pr-6 pl-6">
          <div className="flex flex-col md:flex-row gap-6">
            <div className="md:w-1/3 relative pb-6">
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
                {showNextButton && (
                  <Button
                    onClick={handleNext}
                    disabled={isNextDisabled}
                    className="font-semibold text-base"
                  >
                    {getNextButtonText()}
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
