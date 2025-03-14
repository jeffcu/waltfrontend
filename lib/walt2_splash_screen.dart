// -- lib/walt2_splash_screen.dart
import 'package:flutter/material.dart';
import 'walt2_home_screen.dart';
import 'api_service.dart';
import 'dart:io'; // Import dart:io for File
import 'package:path_provider/path_provider.dart'; // Import path_provider

class Walt2SplashScreen extends StatefulWidget {
  final ApiService apiService;

  const Walt2SplashScreen({super.key, required this.apiService});

  @override
  _Walt2SplashScreenState createState() => _Walt2SplashScreenState();
}

class _Walt2SplashScreenState extends State<Walt2SplashScreen> {
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _fetchInitialData();
  }

  ApiService get _apiService => widget.apiService;

  Future<void> _fetchInitialData() async {
    setState(() {
      _isLoading = true;
    });
    try {
      await _apiService.fetchCsrfToken();
      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      print("Error fetching initial data (CSRF): $e");
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error initializing app: $e")),
      );
    }
  }

  void _beginNewBio() async {
    setState(() {
      _isLoading = true;
    });
    try {
      final initialMessage = await _apiService.getNewBioInitialMessage();
      setState(() {
        _isLoading = false;
      });
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => Walt2HomeScreen(
            initialMessage: initialMessage,
            apiService: _apiService,
          ),
        ),
      );
    } catch (e) {
      print("Error in _beginNewBio: $e");
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error starting new bio: $e")),
      );
    }
  }

  void _loadStory() async {
    setState(() {
      _isLoading = true;
    });
    try {
      final filePath = await _getFilePath();
      final file = File(filePath);
      if (await file.exists()) {
        final storyText = await file.readAsString(); // Load story text

        final continueMessage = await _apiService.continueBio(storyText); // Call continueBio API

        setState(() {
          _isLoading = false;
        });
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => Walt2HomeScreen(
              initialMessage: continueMessage, // Use initial message from API response
              apiService: _apiService,
              // **CHANGE IS HERE: REMOVE loadStoryOnInit: false,**  <--  Ensure this line and below are exactly as shown (commented out)
            ),
          ),
        );
      } else {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("No story file found locally.")),
        );
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      print("Error in _loadStory: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error loading story: $e")),
      );
    }
  }

  Future<String> _getFilePath() async { // Moved _getFilePath to splash screen as it's only used here now
    final directory = await getApplicationDocumentsDirectory();
    return '${directory.path}/walt_biography.txt'; // Default file name
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Walt the auto-Biographer'),
        backgroundColor: Theme.of(context).primaryColor,
        centerTitle: true,
      ),
      body: Stack(
        children: [
          Center(
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Image.asset(
                    'assets/images/walt.png',
                    width: 200,
                    height: 200,
                    fit: BoxFit.contain,
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    "Walt, Your AI Biographer",
                    style: TextStyle(
                      color: Color(0xFF007AFF),
                      fontSize: 32,
                      fontWeight: FontWeight.w600,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    "I want to write your unique story!",
                    style: TextStyle(
                      color: Color(0xFF555555),
                      fontSize: 18,
                      fontStyle: FontStyle.italic,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 40),
                  SizedBox(
                    width: 300,
                    child: ElevatedButton(
                      onPressed: _beginNewBio,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF007AFF),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                      child: const Text("Begin your biography"),
                    ),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: 300,
                    child: ElevatedButton(
                      onPressed: _loadStory,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF007AFF),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                      child: const Text("Load Saved Story"),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_isLoading)
            Positioned.fill(
              child: Container(
                color: Colors.black.withOpacity(0.5),
                child: const Center(
                  child: CircularProgressIndicator(color: Colors.white),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
// -- lib/walt2_splash_screen.dart
