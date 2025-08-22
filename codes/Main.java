import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        
        // Read input string
        String input = sc.nextLine();
        
        // Reverse using StringBuilder
        String reversed = new StringBuilder(input).reverse().toString();
        
        // Print reversed string
        System.out.println(reversed);
    }
}