from transformers import AutoModelForCausalLM, AutoTokenizer


# Class to handle loading the model and tokenizer
class ModelLoader:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None

    def load_model(self):
        """Load the GPT-2 model and tokenizer from the local path"""
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
        return self.model, self.tokenizer


# Service class for text generation
class TextGenerationService:
    def __init__(self, model_loader: ModelLoader):
        self.model, self.tokenizer = model_loader.load_model()

    def generate_text(self, prompt: str, max_new_tokens: int = 100) -> str:
        """Generate text based on the input prompt using GPT-2"""
        # Tokenize the input prompt
        inputs = self.tokenizer(prompt, return_tensors="pt")

        # Get the length of the input_ids
        input_length = inputs["input_ids"].shape[1]

        # Generate the model's response
        output_sequences = self.model.generate(
            input_ids=inputs["input_ids"],
            max_new_tokens=input_length,  # Specify how many new tokens to generate
            num_return_sequences=1,
            no_repeat_ngram_size=2,  # Optional: To prevent repeating sequences
            do_sample=True,  # Optional: To introduce sampling (more creativity)
            temperature=0.1,  # Optional: Controls randomness
        )

        # Decode the output into readable text
        generated_text = self.tokenizer.decode(output_sequences[0], skip_special_tokens=True)
        return generated_text


# Example usage
if __name__ == "__main__":
    model_path = "./path_to_gpt2_model_files"  # Path to your local GPT-2 model folder
    model_loader = ModelLoader(model_path)
    text_generation_service = TextGenerationService(model_loader)

    prompt = "Once upon a time"
    response = text_generation_service.generate_text(prompt, max_length=50)

    print("Generated Response:", response)
