
from file_utils import load_text
from Drafter import Drafter
from Sketcher import Sketcher
import re

def extract_isabelle_proof(text):
    pattern = r'## Proof\s*```isabelle\s*(.*?)```'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        isabelle_proof = match.group(1).strip()
        return isabelle_proof
    else:
        return None
    
def extract_structured_informal_proof(text):
    pattern = r'## Structured informal proof\s*(.*?)\s*(?:##|\Z)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        structured_proof = match.group(1).strip()
        return structured_proof
    else:
        return None

def extract_proof(text):
    proof_pattern = re.compile(r"## Structured informal proof(.*?)## Lemmas", re.DOTALL)
    proof_match = proof_pattern.search(text)
    structured_informal_proof = proof_match.group(1).strip() if proof_match else ""
    
    return structured_informal_proof

def extract_thoughts(text):
    thoughts_codes_pattern = re.compile(r"### Lemma (\d+)\s*(.*?)### Code \1\s*```isabelle(.*?)```", re.DOTALL)
    thoughts_codes_matches = thoughts_codes_pattern.findall(text)
    
    thoughts_codes = []
    for match in thoughts_codes_matches:
        thought_number = match[0]
        thought = match[1].strip()
        code = match[2].strip()
        thoughts_codes.append({
            "thought_number": thought_number,
            "thought": thought,
            "code": code
        })
    return thoughts_codes

def extract_informal_proof(text):
    lines = text.splitlines()
    
    informal_proof = []
    is_in_proof = False
    for line in lines:
        if "Informal Proof" in line:
            is_in_proof = True
            continue
        
        if is_in_proof:
            informal_proof.append(line)
    
    return "\n".join(informal_proof).strip()

def extract_formal_proof_2(text):
    lines = text.split('\n')
    proof_lines = []
    in_proof = False
    proof_keywords = {'lemma', 'theorem', 'proof', 'have', 'then', 'show', 'qed', 'by', 'sledgehammer', 'fixes', 'assumes', 'shows', '(*', 'also', 'finally', 'case', '\"'}

    for i, line in enumerate(lines):
        if 'Formal:' in line:
            in_proof = True
            continue

        if in_proof:
            stripped_line = line.strip()
            if stripped_line == '' or stripped_line.split()[0] in proof_keywords:
                proof_lines.append(line)
            elif line.startswith('    ') or line.startswith('\t'):
                proof_lines.append(line)
            else:
                break

    proof_text = '\n'.join(proof_lines)
    return proof_text


def extract_formal_proof(text):
    proof_lines = []
    in_proof = False

    for line in text.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("Formal:"):
            in_proof = True
            continue
        elif stripped_line.startswith("Informal:"):
            in_proof = False
        elif in_proof:
            if stripped_line == "" and proof_lines:
                continue
            if stripped_line.startswith("This") or stripped_line.startswith("In") or stripped_line.startswith("####################"):
                break
            proof_lines.append(line.rstrip())

    formal_proof = "\n".join(proof_lines)
    return formal_proof

def replace_using_assms_sledgehammer(text):
    lines = text.split('\n')
    output_lines = []
    
    in_statement = False
    has_assumes = False
    pending_has_assumes = False  # Used to handle immediate proofs after the statement

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        if stripped_line.startswith('lemma') or stripped_line.startswith('theorem'):
            in_statement = True
            has_assumes = False
            output_lines.append(line)
            continue

        if in_statement:
            output_lines.append(line)
            if stripped_line.startswith('assumes'):
                has_assumes = True
            # The statement ends when we encounter an empty line or a line that starts the proof
            if stripped_line == '' or stripped_line.startswith('by') or stripped_line.startswith('using') or stripped_line.startswith('proof'):
                in_statement = False
                pending_has_assumes = has_assumes  # Store for immediate proofs
            continue
        
        if stripped_line.startswith('by') or stripped_line.startswith('using'):
            if 'using assms sledgehammer' in line and not pending_has_assumes:
                line = line.replace('using assms sledgehammer', 'sledgehammer')
            elif 'by (simp add: assms)' in line and not pending_has_assumes:
                line = line.replace('by (simp add: assms)', 'by simp')
            output_lines.append(line)
            pending_has_assumes = False  # Reset for the next lemma/theorem
            continue

        if stripped_line.startswith('proof'):
            in_proof = True
            output_lines.append(line)
            continue

        if stripped_line == 'qed':
            in_proof = False
            output_lines.append(line)
            continue

        if 'using assms sledgehammer' in line and not has_assumes:
            line = line.replace('using assms sledgehammer', 'sledgehammer')
        output_lines.append(line)
    
    return '\n'.join(output_lines)

def add_proof_line(formal_statement):
    lines = formal_statement.strip().split('\n')
    has_assumes = False
    output_lines = []
    proof_line_added = False

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        if stripped_line.startswith('assumes'):
            has_assumes = True
            output_lines.append(line)
        
        elif stripped_line.startswith('by'):
            if has_assumes:
                proof_line = '  using assms sledgehammer'
            else:
                proof_line = '  sledgehammer'
            output_lines.append(proof_line)
            proof_line_added = True
        
        elif stripped_line == 'sorry':
            if has_assumes:
                proof_line = '  using assms sledgehammer'
            else:
                proof_line = '  sledgehammer'
            output_lines.append(proof_line)
            proof_line_added = True
        
        else:
            output_lines.append(line)
    
    if not proof_line_added:
        if has_assumes:
            proof_line = '  using assms sledgehammer'
        else:
            proof_line = '  sledgehammer'
        if output_lines[-1].strip() not in ['sledgehammer', 'using assms sledgehammer']:
            output_lines.append(proof_line)

    return '\n'.join(output_lines)

def integrate_lemmas_into_proof(text):
    lines = text.split('\n')
    
    in_helper_lemmas = False
    in_proof_section = False
    
    lemmas = []
    proof = []
    
    current_lemma = []
    
    for line in lines:
        stripped_line = line.strip()
        
        if stripped_line.startswith('## Helper Lemmas'):
            in_helper_lemmas = True
            in_proof_section = False
            continue
        elif stripped_line.startswith('## Proof'):
            in_helper_lemmas = False
            in_proof_section = True
            proof.append(line)
            continue
        
        if in_helper_lemmas:
            if stripped_line == '':
                if current_lemma:
                    lemmas.append('\n'.join(current_lemma))
                    current_lemma = []
            else:
                current_lemma.append(line)
        elif in_proof_section:
            proof.append(line)
    
    if current_lemma:
        lemmas.append('\n'.join(current_lemma))
    
    lemmas_not_in_proof = []
    proof_text = '\n'.join(proof)
    for lemma in lemmas:
        lemma_statement = lemma.strip().split('\n')[0]
        if lemma_statement not in proof_text:
            lemmas_not_in_proof.append(lemma)
    
    if lemmas_not_in_proof:
        for idx, line in enumerate(proof):
            if line.strip().startswith('theorem'):
                theorem_idx = idx
                break
        else:
            theorem_idx = len(proof)
        
        proof_with_lemmas = proof[:theorem_idx] + [''] + lemmas_not_in_proof + [''] + proof[theorem_idx:]
    else:
        proof_with_lemmas = proof
    
    new_text = '\n'.join(proof_with_lemmas)
    return new_text

if __name__ == "__main__":

#     text = """
#     Here is the actual problem. Create a formal proof sketch placing `using assms sledgehammer` in the gaps of the proof sketch, taking inspiration from the previous examples.
# Informal:
# (* ### Problem
# A lemma showing the definition of squaring a real number would be useful for step 1.

# ### Solution
# To prove that the square of a real number \(a\) is equal to \(a \times a\), we start by recalling the definition of squaring in the context of real numbers. The square of a number is defined as the product of that number with itself.

# For any real number \(a\), the square of \(a\) is denoted by \(a^2\). By definition, this means:

# \[ a^2 = a \times a \]

# This is a fundamental property that holds for all real numbers. Therefore, we can conclude that the square of \(a\) is indeed \(a \times a\).

# Thus, we have shown that:

# \[ a^2 = a \times a \]

# which completes the proof. *)

# Formal:
# lemma square_definition:
#   fixes a :: real
#   shows "a^2 = a * a"
#   by simp

# theorem square_real_number:
#   fixes a :: real
#   shows "square a = a * a"
# proof -
#   (* Recall the definition of squaring a real number. *)
#   have "square a = a * a"
#     using square_definition sledgehammer
#   then show ?thesis
#     sledgehammer
# qed

# This proof sketch uses the `lemma` command to define the square of a real number and then uses this lemma in the main theorem to prove the desired result. The `using` command is used to apply the lemma, and `sledgehammer` is used to fill in the remaining details of the proof....
#     """

#     print(extract_formal_proof_2(text))

    input_text = '''## Helper Lemmas
    ```isabelle
    (* lemma 0. A lemma proving the Euclidean algorithm will be beneficial. *)
    lemma euclidean_algorithm:
    fixes a b :: nat
    shows "gcd a b = gcd b (a mod b)"
    proof -
    have "gcd a b = gcd b (a - b * (a div b))"
    sledgehammer
    also have "a - b * (a div b) = a mod b"
    sledgehammer
    finally show ?thesis .
    qed
    ```

    ```isabelle
    (* lemma 1. A lemma showing that the gcd of any number and 1 is 1. *)
    lemma gcd_1:
    fixes a :: nat
    shows "gcd a 1 = 1"
    proof -
    have "gcd a 1 = gcd 1 (a mod 1)"
    sledgehammer
    also have "a mod 1 = 0"
    sledgehammer
    finally show ?thesis
    sledgehammer
    qed
    ```

    ## Proof
    ```isabelle

    (* formal statement copy from the input *)
    theorem imo_1959_p1:
    fixes n :: nat
    shows "gcd (21*n + 4) (14*n + 3) = 1"
    proof -
    (* apply the Euclidean algorithm *)
    have "gcd (21*n + 4) (14*n + 3) = gcd (14*n + 3) ((21*n + 4) mod (14*n + 3))"
    using euclidean_algorithm sledgehammer
    (* show that (21*n + 4) mod (14*n + 3) = 7*n + 1 *)
    then have "gcd (21*n + 4) (14*n + 3) = gcd (14*n + 3) (7*n + 1)"
    sledgehammer
    (* apply the Euclidean algorithm again *)
    then have "gcd (21*n + 4) (14*n + 3) = gcd (7*n + 1) ((14*n + 3) mod (7*n + 1))"
    using euclidean_algorithm sledgehammer
    (* show that (14*n + 3) mod (7*n + 1) = 1 *)
    then have "gcd (21*n + 4) (14*n + 3) = gcd (7*n + 1) 1"
    sledgehammer
    (* use the lemma gcd_1 to conclude that gcd (7*n + 1) 1 = 1 *)
    then show ?thesis
    using gcd_1 sledgehammer
    qed
    ```
    '''
    print(integrate_lemmas_into_proof(input_text))